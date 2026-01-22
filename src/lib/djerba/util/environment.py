"""Functions to handle environment variables"""

import logging
import os
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class directory_finder(logger):

    """Find and validate standard directory paths from environment variables"""
    
    DJERBA_BASE_DIR_VAR = 'DJERBA_BASE_DIR' # defined by Modulator
    DJERBA_RUN_DIR_VAR = 'DJERBA_RUN_DIR'
    DJERBA_PRIVATE_DIR_VAR = 'DJERBA_PRIVATE_DIR'
    DJERBA_TEST_DIR_VAR = 'DJERBA_TEST_DIR'
    DJERBA_TEST_OUTPUT_DIR_VAR = 'DJERBA_TEST_OUTPUT_DIR'
    DJERBA_CORE_HTML_DIR_VAR = 'DJERBA_CORE_HTML_DIR'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)

    def get_directory(self, var):
        value = os.environ.get(var)
        if value == None:
            msg = "No value set for environment variable '{0}'".format(var)
            self.logger.error(msg)
            raise DjerbaEnvDirError(msg)
        elif not self.validator.validate_input_dir(value):
            msg = "Value '{0}' of environment variable '{1}'".format(var, value)+\
                " is not a valid input directory"
            self.logger.error(msg)
            raise DjerbaEnvDirError(msg)
        else:
            msg = "Directory '{0}' from environment variable '{1}' is OK".format(value, var)
            self.logger.debug(msg)
        return value

    def get_base_dir(self):
        return self.get_directory(self.DJERBA_BASE_DIR_VAR)

    def get_core_html_dir(self):
        return self.get_directory(self.DJERBA_CORE_HTML_DIR_VAR)

    def get_data_dir(self):
        return self.get_directory(self.DJERBA_RUN_DIR_VAR)

    def get_private_dir(self):
        return self.get_directory(self.DJERBA_PRIVATE_DIR_VAR)

    def get_test_dir(self):
        return self.get_directory(self.DJERBA_TEST_DIR_VAR)

    def get_test_output_dir(self):
        return self.get_directory(self.DJERBA_TEST_OUTPUT_DIR_VAR)

    def has_valid_directory(self, var):
        dir_ok = True
        value = os.environ.get(var)
        if value == None or not self.validator.validate_input_dir(value):
            dir_ok = False
        return dir_ok

    def has_valid_base_dir(self):
        return self.has_valid_directory(self.DJERBA_BASE_DIR_VAR)

    def has_valid_core_html_dir(self):
        return self.has_valid_directory(self.DJERBA_CORE_HTML_DIR_VAR)

    def has_valid_data_dir(self):
        return self.has_valid_directory(self.DJERBA_RUN_DIR_VAR)

    def has_valid_private_dir(self):
        return self.has_valid_directory(self.DJERBA_PRIVATE_DIR_VAR)

    def has_valid_test_dir(self):
        return self.has_valid_directory(self.DJERBA_TEST_DIR_VAR)

    def has_valid_test_output_dir(self):
        return self.has_valid_directory(self.DJERBA_TEST_OUTPUT_DIR_VAR)    


class DjerbaEnvDirError(Exception):
    pass
