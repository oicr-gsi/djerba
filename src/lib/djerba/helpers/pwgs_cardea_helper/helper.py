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
import djerba.plugins.pwgs.constants as pc

class main(helper_base):

    DEFAULT_CARDEA_URL='https://cardea.gsi.oicr.on.ca/requisition-cases'
    PRIORITY = 20

    def configure(self, config):
        """
        Writes a subset of provenance, and informative JSON files, to the workspace
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        cardea_url = wrapper.get_my_string(pc.CARDEA_URL)
        requisition_id = wrapper.get_my_string(pc.REQ_ID)
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
            assay_name = requisition_json['assayName'].split("-")[0].strip().upper()
            cases = requisition_json['cases']
            if len(cases) > 1 or len(cases) < 1: # only one case expected for clinical 
                msg = "{0} case(s) were found. Only 1 case is expected".format(len(cases))
                raise ValueError(msg)
            else:
                case = requisition_json['cases'][0]
                requisition = case['requisition']
                projects = case['projects']
                root_id = case['donor']['name']
                patient_id = case['donor']['externalName']

            for qc_group in case['qcGroups']:
                if qc_group['libraryDesignCode'] == "PG":
                    group_id = qc_group['groupId']
            
            if len(projects) < 1:
                msg = "No projects were found. 1 project in the 'Accredited' or 'Accredited with Clinical Report' pipeline is required"
                raise ValueError(msg)
            else:
                clinical = "no"
                for project in projects:
                    if "Accredited" in project["pipeline"]:
                        project_id = project['name']
                        clinical = "yes"
                if clinical == "no":
                    print(project['pipeline'])
                    msg = "No projects in the 'Accredited' or 'Accredited with Clinical Report' pipeline were found; 1 is required"
                    raise ValueError(msg)

            for test in case['tests']:
                if test['libraryDesignCode'] == "PG":
                    for fullDepthSequencing in test['fullDepthSequencings']:
                        provenance_id = fullDepthSequencing['name']
                        pg_library_found = True
            if pg_library_found:
                requisition_info = {
                    pc.ASSAY : assay_name,
                    pc.PROJECT: project_id,
                    pc.DONOR: root_id,
                    pc.PATIENT_ID_LOWER: patient_id,
                    pc.PROVENANCE_ID: provenance_id,
                    core_constants.TUMOUR_ID: group_id
                }
                return(requisition_info)
            else:
                msg = "No libraries with code PG were found in requisition {0}".format(requisition_id, test['libraryDesignCode'])
                raise WrongLibraryCodeError(msg)

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default(pc.CARDEA_URL, self.DEFAULT_CARDEA_URL)
        self.add_ini_required(pc.REQ_ID)

    def write_sample_info(self, sample_info):
        self.workspace.write_json(core_constants.DEFAULT_SAMPLE_INFO, sample_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(sample_info))

class MissingCardeaError(Exception):
    pass

class WrongLibraryCodeError(Exception):
    pass
