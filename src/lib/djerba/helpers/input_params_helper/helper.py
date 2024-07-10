import csv
import gzip
import logging
import time
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
    PRIMARY_CANCER = 'primary_cancer'
    SITE_OF_BIOPSY = 'site_of_biopsy'
    REQUISITION_APPROVED = 'requisition_approved'
    ASSAY = 'assay'    
    REQUISITION_ID = 'requisition_id'
    TCGACODE = 'tcgacode'
    SAMPLE_TYPE = 'sample_type'

    # Name for output file
    INPUT_PARAMS_FILE = 'input_params.json'
    
    # Priority
    PRIORITY = 10

    # Permitted assay names
    VALID_ASSAYS = ['WGTS', 'WGS', 'PWGS', 'WGS40X', 'WGTS40X']

    # Other
    NA = "NA"

    def specify_params(self):
        self.logger.debug("Specifying params for input params helper")
        self.set_priority_defaults(self.PRIORITY)

        # All required parameters for input (i.e. from dimsum, req)
        self.add_ini_required(self.DONOR)
        self.add_ini_required(self.PROJECT)
        self.add_ini_required(self.STUDY)
        self.add_ini_required(self.ONCOTREE_CODE)
        self.add_ini_required(self.PRIMARY_CANCER)
        self.add_ini_required(self.SITE_OF_BIOPSY)
        self.add_ini_required(self.REQUISITION_APPROVED)
        self.add_ini_required(self.ASSAY)
        self.add_ini_required(self.REQUISITION_ID)
        self.add_ini_required(self.TCGACODE)
        self.add_ini_required(self.SAMPLE_TYPE)

    def configure(self, config):
        """
        Needs to write the json to the workspace in the configure step
        """
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        
        # No parameters are allowed to be empty
        list_params = [self.DONOR, 
                      self.PROJECT, 
                      self.STUDY, 
                      self.ONCOTREE_CODE, 
                      self.PRIMARY_CANCER,
                      self.SITE_OF_BIOPSY,
                      self.REQUISITION_APPROVED,
                      self.REQUISITION_ID,
                      self.TCGACODE,
                      self.SAMPLE_TYPE,
                      self.ASSAY]

        for param in list_params:
            if wrapper.my_param_is_null(param) or wrapper.get_my_string(param).strip() == "":
                msg = 'Missing required parameter: ' + param + ". Did you forget to enter it?"
                self.logger.error(msg)
                raise RuntimeError(msg)

        # Retrieve the parameters from the ini and write them to the workspace
        info = self.get_input_params(config)
        self.write_input_params_info(info)
        return wrapper.get_config()


    def extract(self, config):
        """
        Write the input params JSON
        """
        self.validate_full_config(config)
        if not self.workspace.has_file(self.INPUT_PARAMS_FILE):
            info = self.get_input_params(config)
            self.write_input_params_info(info)

    def get_input_params(self, config):
        """
        Retrieves values from INI and puts them in a JSON
        """
        try:
            input_params_info = {
                self.DONOR: config[self.identifier][self.DONOR],
                self.STUDY: config[self.identifier][self.STUDY],
                self.PROJECT: config[self.identifier][self.PROJECT],
                self.ONCOTREE_CODE: config[self.identifier][self.ONCOTREE_CODE],
                self.PRIMARY_CANCER: config[self.identifier][self.PRIMARY_CANCER],
                self.SITE_OF_BIOPSY: config[self.identifier][self.SITE_OF_BIOPSY],
                self.REQUISITION_APPROVED: config[self.identifier][self.REQUISITION_APPROVED],
                self.ASSAY: config[self.identifier][self.ASSAY],
                self.REQUISITION_ID: config[self.identifier][self.REQUISITION_ID],
                self.TCGACODE: config[self.identifier][self.TCGACODE],
                self.SAMPLE_TYPE: config[self.identifier][self.SAMPLE_TYPE]
            }
        except KeyError as err:
            msg = "Required config field for input params helper not found: {0}".format(err)
            self.logger.error(err)
            raise
        except ValueError as err:
            # failure to convert config string to float
            msg = "Invalid numeric config value for input params helper: {0}".format(err)
            self.logger.error(err)
            raise
        self.validate_input_params(input_params_info)
        return input_params_info

    def validate_input_params(self, info):
        assay = info.get(self.ASSAY)
        if not assay in self.VALID_ASSAYS and assay != "TAR":
            msg = "Invalid assay '{0}': Must be one of {1}".format(assay, self.VALID_ASSAYS)
            self.logger.error(msg)
            raise ValueError(msg)
        if assay == "TAR":
            msg = "Invalid assay '{0}': Must use [tar_input_params_helper]".format(assay)
            self.logger.error(msg)
            raise ValueError(msg)
        req_approved = info.get(self.REQUISITION_APPROVED)
        try:
            time.strptime(req_approved, '%Y/%m/%d')
        except ValueError as err:
            msg = "Invalid requisition approved date '{0}': ".format(req_approved)+\
                "Must be in yyyy/mm/dd format"
            self.logger.error(msg)
            raise ValueError(msg) from err

    def write_input_params_info(self, input_params_info):
        self.workspace.write_json(self.INPUT_PARAMS_FILE, input_params_info)
        self.logger.debug("Wrote sample info to workspace: {0}".format(input_params_info))
