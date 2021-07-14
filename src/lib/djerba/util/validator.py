"""Validate inputs, eg. by checking filesystem status"""

import logging
import os
import djerba.util.ini_fields as ini
from djerba.util.logger import logger

class config_validator(logger):
    """Check that INI parameters are valid. Input is a ConfigParser object, eg. from an INI file."""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)

    def find_extras(self, config):
        """Find any config arguments unknown to Djerba"""
        unexpected = []
        for title in config.sections():
            if ini.SCHEMA.get(title):
                for parameter in config[title]:
                    if parameter not in ini.SCHEMA[title]:
                        msg = "Unexpected config parameter found: {0}:{1}".format(title, parameter)
                        self.logger.warning(msg)
            else:
                msg = "Unexpected config section found: {0}".format(title)
                self.logger.warning(msg)

    def validate(self, config, section_titles):
        """Validate for the given list of section titles"""
        for title in section_titles:
            if not title in config.sections():
                msg = "[{0}] section not found in config".format(title)
                self.logger.error(msg)
                raise DjerbaConfigError(msg)
            for field in ini.SCHEMA[title]:
                if not config[title].get(field):
                    msg = "[{0}] field '{1}' not found in config".format(title, field)
                    self.logger.error(msg)
                    raise DjerbaConfigError(msg)
        return True

    def validate_full(self, config):
        """Config has all parameters; valid input for extract step"""
        valid = self.validate(config, [ini.INPUTS, ini.SEG, ini.SETTINGS, ini.DISCOVERED])
        self.find_extras(config)
        self.logger.info("Successfully validated fully-specified Djerba config")
        return valid

    def validate_minimal(self, config):
        """Config has minimal required parameters; valid input for configure step"""
        valid = self.validate(config, [ini.INPUTS])
        self.find_extras(config)
        self.logger.info("Successfully validated minimal Djerba config")
        return valid

class path_validator:

    """Check that inputs are valid; if not, raise an error"""

    # TODO instead of raising an error, could log outcome and return boolean

    def __init__(self):
        pass        

    def validate_input_dir(self, path):
        """Confirm an input directory exists and is readable"""
        valid = False
        if not os.path.exists(path):
            raise OSError("Input path %s does not exist" % path)
        elif not os.path.isdir(path):
            raise OSError("Input path %s is not a directory" % path)
        elif not os.access(path, os.R_OK):
            raise OSError("Input path %s is not readable" % path)
        else:
            valid = True
        return valid
    
    def validate_input_file(self, path):
        """Confirm an input file exists and is readable"""
        valid = False
        if not os.path.exists(path):
            raise OSError("Input path %s does not exist" % path)
        elif not os.path.isfile(path):
            raise OSError("Input path %s is not a file" % path)
        elif not os.access(path, os.R_OK):
            raise OSError("Input path %s is not readable" % path)
        else:
            valid = True
        return valid
        
    def validate_output_dir(self, path):
        """Confirm an output directory exists and is writable"""
        valid = False
        if not os.path.exists(path):
            raise OSError("Output path %s does not exist" % path)
        elif not os.path.isdir(path):
            raise OSError("Output path %s is not a directory" % path)
        elif not os.access(path, os.W_OK):
            raise OSError("Output path %s is not writable" % path)
        else:
            valid = True
        return valid

    def validate_output_file(self, path):
        """Confirm an output file can be written"""
        valid = False
        if os.path.isdir(path):
            raise OSError("Output file %s cannot be a directory" % path)
        elif os.path.exists(path) and not os.access(path, os.W_OK):
            raise OSError("Output file %s exists and is not writable" % path)
        else:
            parent = os.path.dirname(os.path.realpath(path))
            try:
                valid = self.validate_output_dir(parent)
            except OSError as err:
                raise OSError("Parent directory of output path %s is not valid" % path) from err
        return valid
    
    def validate_present(self, config, section, param):
        # throws a KeyError if param is missing; TODO informative error message
        return config[section][param]

class DjerbaConfigError(Exception):
    pass

