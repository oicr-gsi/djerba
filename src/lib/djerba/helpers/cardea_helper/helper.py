"""
Helper for writing a subset of cardea to the shared workspace
"""

import os
import csv
import gzip
import logging
import requests
import json
import re
import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini 
from djerba.helpers.base import helper_base
import djerba.helpers.cardea_helper.constants as constants

class main(helper_base):

    DEFAULT_CARDEA_URL='https://cardea.gsi.oicr.on.ca/requisition-cases'
    PRIORITY = 20
    
    ASSAY_MAP = {
        # Clinical Assays
        "WGS - 80XT/30XN": "WG",
        "WGS - 40XT/30XN": "WG",
        "WGTS - 80XT/30XN": "WG",
        "WGTS - 40XT/30XN": "WG",
        "REVOLVE - cfDNA+BC": "TS",

        # RUO Assays
        "RUO WGS - 80XT/30XN": "WG",
        "RUO WGS - 40XT/30XN": "WG",
        "RUO WGTS - 80XT/30XN": "WG",
        "RUO WGTS - 40XT/30XN": "WG",
        "RUO REVOLVE - cfDNA+BC": "TS"
    }


    def configure(self, config):
        """
        Writes a subset of provenance, and informative JSON files, to the workspace
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        
        # Get parameters from config
        cardea_url = wrapper.get_my_string(constants.CARDEA_URL)
        requisition_id = wrapper.get_my_string(constants.REQ_ID)
        attributes = wrapper.get_my_string(core_constants.ATTRIBUTES)

        # Research often crams multiple donors into one requisition.
        # In order to get information from a research requisition, you'll need to get the case associated with a known donor.
        # So, research cases must specify donors.
        # Clinical cases only have 1 case per requisition, so the donor can be found normally.
        if 'research' in attributes:
            if wrapper.my_param_is_null(constants.DONOR):
                msg = "To generate a research report, the donor must be manually specified." 
                self.logger.error(msg)
                raise UnknownDonorError(msg)
            else:
                donor = wrapper.get_my_string(constants.DONOR)
        else:
            donor = None # Don't need it right now
        
        sample_info = self.get_cardea(requisition_id, cardea_url, attributes, donor)

        # Add donor to config (the only manually specifiable parameter aside from requisition_id and attributes, as research reports require it) 
        if wrapper.my_param_is_null(constants.DONOR):
            wrapper.set_my_param(constants.DONOR, sample_info[constants.DONOR])

        # Write the sample information
        self.write_sample_info(sample_info)
        return wrapper.get_config()

    def extract(self, config):
        self.validate_full_config(config)

    def get_cardea(self, requisition_id, cardea_url, attributes, donor):
        pg_library_found = False
        
        
        url = "/".join((cardea_url, requisition_id))
        r = requests.get(url, allow_redirects=True)
        if r.status_code == 404:
            msg = "The requisition {0} was not found on Cardea".format(requisition_id)
            raise MissingCardeaError(msg)
        else:
            # Get the requisition
            requisition_json = json.loads(r.text)
            
            # Uncomment this when debugging if you want to view the requisition that was printed.
            #self.workspace.write_json("test_requisition.json", requisition_json)

            # Get the case
            case = self.get_case(requisition_json, requisition_id, attributes, donor)

            # From the case, get the requisition info.
            requisition_info = self.get_requisition_info(case, requisition_id, attributes)

            return(requisition_info)



    def get_case(self, requisition_json, requisition_id, attributes, donor):
        """
        Retrieves the case.
        Research: often many cases to one requisition, and require donor to get the correct case.
        Clinical: exactly 1 case (i.e. 1 donor) per requisition.
        """

        # Case 1: Regardless of clinical or research, there are no cases.
        if len(requisition_json) == 0:  
            msg = "0 cases were found. If this is a clinical report, exactly 1 case is expected. If this is a research report, at least 1 case is expected."
            self.logger.error(msg)
            raise RequisitionError(msg)
        # Case 2: it's a research report, and donor is given (if not given, there will be an error upstream).
        elif donor and 'research' in attributes:
            case_found = False
            for requisition_piece in requisition_json:
                if donor == requisition_piece['donor']['name'] and 'RUO' in requisition_piece['assayName']:
                    case = requisition_piece
                    case_found = True
            if not case_found:
                msg = "Could not find case in research requisition {0} for given donor {1}. Did you misspell the donor name?".format(requisition_id, donor)
                self.logger.error(msg)
                raise RequisitionError(msg)
        # Case 3: it's a clinical report, but there's more than one case.
        elif 'clinical' in attributes and len(requisition_json) > 1:
            msg = "{0} cases were found. Only 1 case per requisition is expected for a clinical report.".format(len(requisition_json))
            self.logger.error(msg)
            raise RequisitionError(msg)
        # Case 4: It's a clinical report, and there's exactly 1 case (whether donor is given or not).
        else:
            case = requisition_json[0]
        
        return case

    def get_requisition_info(self, case, requisition_id, attributes):
        """
        Gets the requisition info.
        """
        assay_name = case['assayName']
        assay = assay_name.split("-")[0].strip().upper() 
        requisition_approved = case['startDate']
        projects = case['projects']
        donor = case['donor']['name']
        patient_id = case['donor']['externalName'].split(',')[0].strip()
        tumour_id, normal_id = self.get_tumour_normal_ids(requisition_id, case, assay_name)
        project_id = self.get_project_id(requisition_id, projects, attributes)
        sample_name_whole_genome_tumour, sample_name_whole_genome_normal, sample_name_whole_transcriptome = self.get_library_ids(requisition_id, case, assay)

        requisition_info = {
            constants.ASSAY : assay,
            constants.PROJECT: project_id,
            constants.DONOR: donor,
            constants.PATIENT_ID: patient_id,
            constants.REQ_APPROVED: requisition_approved,
            constants.REQ_ID: requisition_id,
            constants.SAMPLE_NAME_WHOLE_GENOME_TUMOUR: sample_name_whole_genome_tumour,
            constants.SAMPLE_NAME_WHOLE_GENOME_NORMAL: sample_name_whole_genome_normal,
            constants.SAMPLE_NAME_WHOLE_TRANSCRIPTOME: sample_name_whole_transcriptome,
            constants.TUMOUR_ID: tumour_id,
            constants.NORMAL_ID: normal_id
        }

        return requisition_info

    def get_qc_ids(self, qc_group, assay_name, requisition_id):
        """
        Determine normal and tumour IDs based on assay type and qc_group.
        Returns a tuple: (normal_id, tumour_id) with either normal or tumour ID; other will be None.
        """
        
        if assay_name in self.ASSAY_MAP:
            if qc_group['libraryDesignCode'] == self.ASSAY_MAP[assay_name]:
                if qc_group['tissueType'] == "R": # assumes all R is normal
                    return (None, qc_group['groupId']) 
                else: # assumes anything else is tumour (T, M, and other) 
                    return (qc_group['groupId'], None)
            else:
                return (None, None)
        else:
            msg = "Unexpected assay {0} for requisition {1}. Must be one of: [WGS - 80XT/30XN, WGS - 80XT/30XN, WGS - 80XT/30XN, WGS - 80XT/30XN, REVOLVE - cfDNA+BC].".format(assay_name, requisition_id)
            self.logger.error(msg)
            raise UnknownAssayError(msg)

    def get_tumour_normal_ids(self, requisition_id, case, assay_name):
        """
        Returns tumor and normal IDs.
        """

        ids = [None, None] # tumour_id, normal_id

        self.logger.info("Finding tumour and normal IDs for assay {0}".format(assay_name))
        
        for qc_group in case['qcGroups']:
            # Get the normal and tumour IDs.
            normal_id, tumour_id = self.get_qc_ids(qc_group, assay_name, requisition_id)
            # Update IDs as we find them. Don't overwrite the found IDs.
            ids = [
                tumour_id if tumour_id else ids[0],    
                normal_id if normal_id else ids[1]
            ]


        tumour_id, normal_id = ids
        if not tumour_id or not normal_id: # if either or both are None
            msg = "Could not find one of tumour ({0}) or normal ({1}) IDs for assay {2} and requisition {3}.".format(tumour_id, normal_id, assay_name, requisition_id)
            self.logger.error(msg)
            raise MissingIdError(msg)

        return tumour_id, normal_id 

    def get_library_ids(self, requisition_id, case, assay):
        """
        Gets the following IDs:
        - sample_name_whole_genome_normal
        - sample_name_whole_genome_tumour
        - sample_name_whole_transcriptome
        """
        # Sometimes, a library can fail.
        # If a library fails, under libraryQualifications, there will be more than one entry.
        # Only take the entry in which qcPassed = 'true', or qcReason = 'Passed'

        sample_name_whole_genome_normal = "None"
        sample_name_whole_genome_tumour = "None"
        sample_name_whole_transcriptome = "None"
        
        library_count = 0
        for test in case['tests']:
            # For WGTS and WGS, expect three tests: 0 (WG normal), 1 (WT), 2 (WG tumour)
            # Unsure if the order of these is preserved. Better not to assume.
            if test['name'] == "Normal WG":
                sample_name_whole_genome_normal = test['fullDepthSequencings'][0]['name']
                library_count += 1
            elif test['name'] == "Tumour WG":
                sample_name_whole_genome_tumour = test['fullDepthSequencings'][0]['name']
                library_count += 1
            elif test['name'] == "Tumour WT":
                sample_name_whole_transcriptome = test['fullDepthSequencings'][0]['name']
                library_count += 1
        # WGS will not have a Tumour WT. Manually assign it a placeholder.
        if assay == "WGS":
            sample_name_whole_transcriptome = "whole_transcriptome_placeholder"
            library_count += 1
        # TAR (actually called REVOLVE in Cardea) does not require library IDs.
        if assay == "REVOLVE":
            for test in case['tests']:
                # For TAR, expect three tests: Normal TS, Tumour SW, Tumour TS
                # Unsure if the order of these is preserved. Better not to assume.
                if test['name'] == "Normal TS":
                    sample_name_whole_genome_normal = test['fullDepthSequencings'][0]['name']
                    library_count += 1
                elif test['name'] == "Tumour SW":
                    sample_name_whole_genome_tumour = test['fullDepthSequencings'][0]['name']
                    library_count += 1
                elif test['name'] == "Tumour TS":
                    sample_name_whole_transcriptome = test['fullDepthSequencings'][0]['name']
                    library_count += 1

        # There should be 3 libraries (3 for WGTS, 2+1 placeholder for WGS)
        if library_count == 3:
            return sample_name_whole_genome_normal, sample_name_whole_genome_tumour, sample_name_whole_transcriptome
        else:
            msg = "One of the following libraries was not found in requisition {0}: sample_name_whole_genome_tumour ({1}), sample_name_whole_genome_normal ({2}), sample_name_whole_transcriptome ({3}).".format(
                    requisition_id,
                    sample_name_whole_genome_normal,
                    sample_name_whole_genome_tumour,
                    sample_name_whole_transcriptome
            )

            raise MissingLibraryError(msg)

    def get_project_id(self, requisition_id, projects, attributes):
        """
        There may be more than one project.
        Example: a project can have Accredited with Clinical Report, Accredited, Research
        We only want Accredited with Clinical Report...for now.
        """

        project_found = False       
        clinical_projects = [] # Count how many projects have pipeline "Accredited with Clinical Report"
        research_projects = []
        for project in projects:
            if "clinical" in attributes:
                if project['pipeline'] == "Accredited with Clinical Report":
                    project_id = project['name']
                    pipeline_name = project['pipeline']
                    clinical_projects.append(project_id) 
                    project_found = True
            elif 'research' in attributes:
                if project['pipeline'] == "Research":
                    project_id = project['name']
                    pipeline_name = project['pipeline']
                    research_projects.append(project_id) 
                    project_found = True
        if len(clinical_projects) > 1 or len(research_projects) > 1: # There should only be one project with pipeline "Accredited with Clinical Report"
            project_id = projects[0]['name']
            msg = "Found more than one project associated with the pipeline '{0}' for requisition {1}." \
                  " Defaulting to the first project: {2}." \
                  " If this project is incorrect, please manually specify the correct project.".format(pipeline_name, requisition_id, project_id)
            self.logger.warning(msg)
        if not project_found:
            msg = "Could not find project in requisition {0}. You may have to manually specify the project.".format(requisition_id)
            self.logger.error(msg)
            raise MissingProjectError(msg) 
        return project_id


    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        # Set defaults
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default(constants.CARDEA_URL, self.DEFAULT_CARDEA_URL)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        # You MUST provide a requisition ID.
        self.add_ini_required(constants.REQ_ID)
        # Donor is the only parameter that can be manually specified if need be.
        self.add_ini_discovered(constants.DONOR)


    def write_sample_info(self, sample_info):
        self.workspace.write_json(core_constants.DEFAULT_SAMPLE_INFO, sample_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(sample_info))

class MissingCardeaError(Exception):
    pass

class MissingIdError(Exception):
    pass

class MissingLibraryError(Exception):
    pass

class MissingProjectError(Exception):
    pass
    
class RequisitionError(Exception):
    pass

class UnknownAssayError(Exception):
    pass
    
class UnknownDonorError(Exception):
    pass
