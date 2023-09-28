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

    # Required parameter names for INI
    DONOR = 'donor'
    STUDY = 'study'
    PROJECT = 'project'
    ONCOTREE_CODE = 'oncotree_code'
    PATIENT_STUDY_ID = 'patient_study_id'
    TUMOUR_ID = 'tumour_id'
    NORMAL_ID = 'normal_id'
    PRIMARY_CANCER = 'primary_cancer'
    SITE_OF_BIOPSY = 'site_of_biopsy'
    KNOWN_VARIANTS = 'known_variants'
    REQUISITION_APPROVED = 'requisition_approved'
    ASSAY = 'assay'

    # Name for output file
    INPUT_PARAMS_FILE = 'input_params.json'
    
    # Priority
    PRIORITY = 10


    def specify_params(self):
        self.logger.debug("Specifying params for input params helper")
        self.set_priority_defaults(self.PRIORITY)

        # All required parameters for input (i.e. from dimsum, req)
        self.add_ini_required(self.DONOR)
        self.add_ini_required(self.PROJECT)
        self.add_ini_required(self.STUDY)
        self.add_ini_required(self.ONCOTREE_CODE)
        self.add_ini_required(self.PATIENT_STUDY_ID)
        self.add_ini_required(self.TUMOUR_ID)
        self.add_ini_required(self.NORMAL_ID)
        self.add_ini_required(self.PRIMARY_CANCER)
        self.add_ini_required(self.SITE_OF_BIOPSY)
        self.add_ini_required(self.KNOWN_VARIANTS)
        self.add_ini_required(self.REQUISITION_APPROVED)
        self.add_ini_required(self.ASSAY)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)

        # Retrieve the parameters from the ini
        info = self.get_input_params(config)

        # Write them to a json
        self.write_input_params_info(info)

        return wrapper.get_config()

    def extract(self, config):
        self.validate_full_config(config)

    def get_input_params(self, config):
        input_params_info = {
            
            self.DONOR: config[self.identifier][self.DONOR],
            self.STUDY: config[self.identifier][self.STUDY],
            self.PROJECT: config[self.identifier][self.PROJECT],
            self.ONCOTREE_CODE: config[self.identifier][self.ONCOTREE_CODE],
            self.PATIENT_STUDY_ID: config[self.identifier][self.PATIENT_STUDY_ID],
            self.TUMOUR_ID: config[self.identifier][self.TUMOUR_ID],
            self.NORMAL_ID: config[self.identifier][self.NORMAL_ID],
            self.PRIMARY_CANCER: config[self.identifier][self.PRIMARY_CANCER],
            self.SITE_OF_BIOPSY: config[self.identifier][self.SITE_OF_BIOPSY],
            self.KNOWN_VARIANTS: config[self.identifier][self.KNOWN_VARIANTS],
            self.REQUISITION_APPROVED: config[self.identifier][self.REQUISITION_APPROVED],
            self.ASSAY: config[self.identifier][self.ASSAY],
        }
        return input_params_info

    def write_input_params_info(self, input_params_info):
        self.workspace.write_json(self.INPUT_PARAMS_FILE, input_params_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(input_params_info))
