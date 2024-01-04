"""
Helper for writing a subset of file provenance to the shared workspace
Outputs to the workspace:
- Subset of sample provenance for the donor and study supplied by the user
- JSON file with donor, study, and sample names
Plugins can then create their own provenance reader objects using params in the JSON, to
find relevant file paths. Reading the provenance subset is very much faster than reading 
the full file provenance report.
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
        cardea_url = wrapper.get_my_string('cardea_url')
        requisition_id = wrapper.get_my_string('requisition_id')
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
            for case in requisition_json['cases']:
                requisition = case["requisition"]
                projects = case["projects"]
            for qc_group in requisition['qcGroups']:
                group_id = qc_group['groupId']
                root_id = qc_group['donor']['name']
                patient_id = qc_group['donor']['externalName']
            for project in projects:
                project_id = project["name"]
            for test in case["tests"]:
                if test["libraryDesignCode"] == "PG":
                    for fullDepthSequencing in test["fullDepthSequencings"]:
                        provenance_id = fullDepthSequencing['name']
                        pg_library_found = True
            if pg_library_found:
                requisition_info = {
                    'assay_name' : requisition_json["assayName"],
                    'project': project_id,
                    'donor': root_id,
                    'patient_study_id': patient_id,
                    'provenance_id': provenance_id,
                    core_constants.TUMOUR_ID: group_id
                }
                return(requisition_info)
            else:
                msg = "No libraries with code PG were found in requisition {0}".format(requisition_id, test["libraryDesignCode"])
                raise WrongLibraryCodeError(msg)


    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default('cardea_url', self.DEFAULT_CARDEA_URL)
        self.add_ini_required('requisition_id')

    def write_sample_info(self, sample_info):
        self.workspace.write_json(core_constants.DEFAULT_SAMPLE_INFO, sample_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(sample_info))

class MissingCardeaError(Exception):
    pass

class WrongLibraryCodeError(Exception):
    pass