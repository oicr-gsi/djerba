"""Validate inputs, eg. by checking filesystem status"""

import logging
import os
import re
from time import sleep
from djerba.util.logger import logger

class path_validator(logger):

    """Check that inputs are valid; if not, raise an error"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)

    def _process_error_message(self, message):
        """If message is not empty, log it and raise an error"""
        if message:
            valid = False
            self.logger.error(message)
            raise OSError(message)
        else:
            valid = True
        return valid

    def validate_input_dir(self, path):
        """Confirm an input directory exists and is readable"""
        if not isinstance(path, str):
            error = "Input path '%s' is not a string" % path
        elif not os.path.exists(path):
            error = "Input path %s does not exist" % path
        elif not os.path.isdir(path):
            error = "Input path %s is not a directory" % path
        elif not os.access(path, os.R_OK):
            error = "Input path %s is not readable" % path
        else:
            error = None
        return self._process_error_message(error)
    
    def validate_input_file(self, path):
        """Confirm an input file exists and is readable"""
        if not path:
            error = "Input path '%s' is not a valid path value" % path
        elif not os.path.exists(path):
            error = "Input path %s does not exist" % path
        elif not os.path.isfile(path):
            error = "Input path %s is not a file" % path
        elif not os.access(path, os.R_OK):
            error = "Input path %s is not readable" % path
        else:
            error = None
        return self._process_error_message(error)
        
    def validate_output_dir(self, path):
        """Confirm an output directory exists and is writable"""
        if not path:
            error = "Output path '%s' is not a valid path value" % path
        elif not os.path.exists(path):
            error = "Output path %s does not exist" % path
        elif not os.path.isdir(path):
            error = "Output path %s is not a directory" % path
        elif not os.access(path, os.W_OK):
            error = "Output path %s is not writable" % path
        else:
            error = None
        return self._process_error_message(error)

    def validate_output_file(self, path):
        """Confirm an output file can be written"""
        error = None
        if not path:
            error = "Output path '%s' is not a valid path value" % path
        elif os.path.isdir(path):
            error = "Output file %s cannot be a directory" % path
        elif os.path.exists(path) and not os.access(path, os.W_OK):
            error = "Output file %s exists and is not writable" % path
        elif not os.path.exists(path):
            parent = os.path.dirname(os.path.realpath(path))
            try:
                valid = self.validate_output_dir(parent)
            except OSError as err:
                error = "Parent directory of output path {0} is not valid: {1}".format(path, err)
        return self._process_error_message(error)
    
    def validate_present(self, config, section, param):
        # throws a KeyError if param is missing; TODO informative error message
        return config[section][param]


class waiting_path_validator(logger):
    """If path is not found, wait in case of a race condition"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)

    def input_path_exists(self, path):
        """Check if an input path exists"""
        if not path:
            error = "Input path '%s' is not a valid path value" % path
            self.logger.error(msg)
            raise OSError(msg)
        path_exists = False
        for interval in [0.1, 1, 5]:
            if os.path.exists(path):
                path_exists = True
                break
            msg = "Path {0} not found, waiting {1} second(s)".format(path, interval)
            self.logger.debug(msg)
            sleep(interval)
        if path_exists:
            self.logger.debug("Path '{0}' exists".format(path))
        else:
            self.logger.debug("Path '{0}' not found within the waiting period".format(path))
        return path_exists


class DjerbaConfigError(Exception):
    pass

