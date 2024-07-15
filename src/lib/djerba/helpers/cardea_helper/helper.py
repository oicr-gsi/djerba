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
            self.workspace.write_json("wgts_requisition.json", requisition_json)
            if len(requisition_json) != 1: # only one case expected per requisition for clinical 
                msg = "{0} case(s) were found. Only 1 case is expected".format(len(requisition_json))
                self.logger.error(msg)
                raise ValueError(msg)
            else:
                case = requisition_json[0]
                try:
                    assay_name = case['assayName'].split("-")[0].strip().upper() 
                except (KeyError, IndexError) as err:
                    msg = "Unexpected format for Cardea results: {0}".format(err)
                    self.logger.error(msg)
                    raise ValueError(msg) from err
                requisition = case['requisition']
                requisition_approved = case['startDate'].replace("-", "/")
                projects = case['projects']
                donor = case['donor']['name']
                patient_id = case['donor']['externalName'].split(',')[0].strip()

            for qc_group in case['qcGroups']:
                # WGTS and WGS assays will use "WG" as the library design code.
                if qc_group['libraryDesignCode'] == "WG" and assay_name == "WGS" 
                    # The tissue type for blood is always R. For tumour, it varies (ex. M, P, other?).
                    if qc_group['tissueType'] == "R":
                        normal_id = qc_group['groupId']
                    elif qc_group['tissueType'] != "R":
                        tumour_id = qc_group['groupId']
                elif qc_group['libraryDesignCode'] == "SW":
            
            if len(projects) < 1:
                msg = "No projects were found. 1 project in the 'Accredited' or 'Accredited with Clinical Report' pipeline is required"
                self.logger.error(msg)
                raise ValueError(msg)
            else:
                clinical = False
                for project in projects:
                    if "Accredited" in project["pipeline"]:
                        project_id = project['name']
                        clinical = True
                if clinical == False:
                    print(project['pipeline'])
                    msg = "No projects in the 'Accredited' or 'Accredited with Clinical Report' pipeline were found; 1 is required"
                    self.logger.error(msg)
                    raise ValueError(msg)

            
            # Sometimes, a library can fail.
            # If a library fails, under libraryQualifications, there will be more than one entry.
            # Only take the entry in which qcPassed = 'true', or qcReason = 'Passed'
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
            if assay_name == "WGS":
                sample_name_whole_transcriptome = "whole_transcriptome_placeholder"
                library_count += 1
            # TAR (actually called REVOLVE in Cardea) does not require library IDs. 
            if assay_name == "REVOLVE":
                sample_name_whole_genome_normal = "None"
                sample_name_whole_genome_tumour = "None"
                sample_name_whole_transcriptome = "None"
                library_count += 3

            # There should be 3 libraries (3 for WGTS, 2+1 placeholder for WGS)
            if library_count == 3:
                requisition_info = {
                    constants.ASSAY : assay_name,
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
            else:
                msg = "One of the following libraries was not found in requisition {0}: sample_name_whole_genome_tumour, sample_name_whole_genome_normal, sample_name_whole_transcriptome.".format(requisition_id, test['libraryDesignCode'])
                raise MissingLibraryCodeError(msg)
                    
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

class MissingLibraryCodeError(Exception):
    pass
