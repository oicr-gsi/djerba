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
        "WGS - 80XT/30XN": "WG",
        "WGS - 40XT/30XN": "WG",
        "WGTS - 80XT/30XN": "WG",
        "WGTS - 40XT/30XN": "WG",
        "REVOLVE - cfDNA+BC": "TS",
    }


    def configure(self, config):
        """
        Writes a subset of provenance, and informative JSON files, to the workspace
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        cardea_url = wrapper.get_my_string(constants.CARDEA_URL)
        requisition_id = wrapper.get_my_string(constants.REQ_ID)
        sample_info = self.get_cardea(requisition_id, cardea_url)
        self.write_sample_info(sample_info)
        return wrapper.get_config()

    def extract(self, config):
        self.validate_full_config(config)

    def get_cardea(self, requisition_id, cardea_url):
        pg_library_found = False
        url = "/".join((cardea_url, requisition_id))
        r = requests.get(url, allow_redirects=True)
        if r.status_code == 404:
            msg = "The requisition {0} was not found on Cardea".format(requisition_id)
            raise MissingCardeaError(msg)
        else:
            requisition_json = json.loads(r.text)

            # Uncomment this when debugging if you want to view the requisition that was printed.
            #self.workspace.write_json("test_requisition.json", requisition_json)
            
            if len(requisition_json) != 1: # only one case expected per requisition for clinical 
                msg = "{0} case(s) were found. Only 1 case is expected".format(len(requisition_json))
                self.logger.error(msg)
                raise ValueError(msg)
            else:
                case = requisition_json[0]
                try:
                    assay_name = case['assayName']
                    assay = assay_name.split("-")[0].strip().upper() 
                except (KeyError, IndexError) as err:
                    msg = "Unexpected format for Cardea results: {0}".format(err)
                    self.logger.error(msg)
                    raise ValueError(msg) from err
                requisition = case['requisition']
                requisition_approved = case['startDate']
                projects = case['projects']
                donor = case['donor']['name']
                patient_id = case['donor']['externalName'].split(',')[0].strip()
                tumour_id, normal_id = self.get_tumour_normal_ids(requisition_id, case, assay_name)
                project_id = self.get_project_id(requisition_id, projects)
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

            return(requisition_info)


    def find_qc_ids(self, qc_group, assay_name, requisition_id):
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
            normal_id, tumour_id = self.find_qc_ids(qc_group, assay_name, requisition_id)
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
            # IDs already set to None.
            library_count += 3

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

    def get_project_id(self, requisition_id, projects):
        """
        There may be more than one project.
        Example: a project can have Accredited with Clinical Report, Accredited, Research
        We only want Accredited with Clinical Report...for now.
        """

        project_found = False
        for project in projects:
            if project['pipeline'] == "Accredited with Clinical Report":
                project_id = project['name']
                project_found = True
                return project_id
        if not project_found:
            msg = "Could not find pipeline 'Accredited with Clinical Report' in requisition {0}.".format(requisition_id)
            self.logger.error(msg)
            raise MissingProjectError(msg) 


    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default(constants.CARDEA_URL, self.DEFAULT_CARDEA_URL)
        self.add_ini_required(constants.REQ_ID)

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

class UnknownAssayError(Exception):
    pass
