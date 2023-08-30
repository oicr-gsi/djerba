"""
Helper for writing a subset of file provenance to the shared workspace

Outputs to the workspace:
- Subset of sample provenance for the donor and study supplied by the user
- JSON file with donor, study, and sample names

Plugins can then create their own provenance reader objects using params in the JSON, to
find relevant file paths. Reading the provenance subset is very much faster than reading 
the full file provenance report.
"""

import csv
import gzip
import logging
import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini  # TODO new module for these constants?
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base
from djerba.util.provenance_reader import provenance_reader, sample_name_container, \
    InvalidConfigurationError

class main(helper_base):

    ROOT_SAMPLE_NAME = 'root_sample_name'
    PROJECT = 'project'
    ONCOTREE_CODE = 'oncotree_code'
    TUMOUR_ID = 'tumour_id'
    NORMAL_ID = 'normal_id'
    PRIORITY = 50


    def configure(self, config):
        """
        Writes a subset of provenance, and a sample info JSON file, to the workspace
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        sample_info = {
            self.ROOT_SAMPLE_NAME: wrapper.get_my_string(self.ROOT_SAMPLE_NAME),
            self.PROJECT:  wrapper.get_my_string(self.PROJECT),
            self.ONCOTREE_CODE:  wrapper.get_my_string(self.ONCOTREE_CODE),
            self.TUMOUR_ID:  wrapper.get_my_string(self.TUMOUR_ID),
            self.NORMAL_ID:  wrapper.get_my_string(self.NORMAL_ID)
        }
        self.write_input_parameters(sample_info)
        return config

    def extract(self, config):
        """
        If not already in the workspace, write the provenance subset and sample info JSON
        """
        self.validate_full_config(config)
        wrapper = self.get_config_wrapper(config)
        

    #def get_input_parameters(self, config):
    #    """
    #    Parse file provenance and populate the sample info data structure
    #    If the sample names are unknown, get from file provenance given study and donor
    #    """
    #    )
    #    names = reader.get_sample_names()
    #    ids = reader.get_identifiers()
    #    sample_info = {
    #        self.ROOT_SAMPLE_NAME: wrapper.get_my_string(self.ROOT_SAMPLE_NAME),
    #        self.PROJECT:  wrapper.get_my_string(self.PROJECT),
    #        self.ONCOTREE_CODE:  wrapper.get_my_string(self.ONCOTREE_CODE),
    #        self.TUMOUR_ID:  wrapper.get_my_string(self.TUMOUR_ID),
    #        self.NORMAL_ID:  wrapper.get_my_string(self.NORMAL_ID)
    #    }
    #    return sample_info

    def specify_params(self):
        self.logger.debug("Specifying params for provenance helper")
        self.set_priority_defaults(self.PRIORITY)
        self.add_ini_required(self.ROOT_SAMPLE_NAME)
        self.add_ini_required(self.PROJECT)
        self.add_ini_required(self.ONCOTREE_CODE)
        self.add_ini_required(self.TUMOUR_ID)
        self.add_ini_required(self.NORMAL_ID)

    def write_input_parameters(self, sample_info):
        self.workspace.write_json(core_constants.DEFAULT_SAMPLE_INFO, sample_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(sample_info))
