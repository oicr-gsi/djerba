"""Validate inputs, eg. by checking filesystem status"""

import logging
import os
import re
import djerba.util.ini_fields as ini
from djerba.util.logger import logger

class config_validator(logger):
    """Check that INI parameters are valid. Input is a ConfigParser object, eg. from an INI file."""

    def __init__(self, wgs_only, failed, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.wgs_only = wgs_only
        if failed:
            self.logger.info("Validating config for failed report; requirements are the same for WGS-only and WGTS")
            self.schema = ini.SCHEMA_FAILED
        elif wgs_only:
            self.logger.info("Validating config for WGS-only report")
            self.schema = ini.SCHEMA_WGS_ONLY
        else:
            self.logger.info("Validating config for WGTS report")
            self.schema = ini.SCHEMA_DEFAULT

    def find_extras(self, config):
        """Find any config arguments unknown to Djerba"""
        unexpected = []
        for title in config.sections():
            if self.schema.get(title):
                for parameter in config[title]:
                    # INI names are case-insensitive, so the comparison must be too
                    p = parameter.casefold()
                    if not any([p==q.casefold() for q in self.schema[title]]):
                        msg = "Unexpected config parameter found: {0}:{1}".format(title, parameter)
                        self.logger.warning(msg)
            else:
                msg = "Unexpected config section found: {0}".format(title)
                self.logger.warning(msg)

    def validate(self, config, section_titles):
        """Validate for the given list of section titles"""
        for section in section_titles:
            if not section in config.sections():
                msg = "[{0}] section not found in config".format(section)
                self.logger.error(msg)
                raise DjerbaConfigError(msg)
            for field in self.schema[section]:
                if not config[section].get(field):
                    msg = "[{0}] field '{1}' not found in config".format(section, field)
                    self.logger.error(msg)
                    raise DjerbaConfigError(msg)
        # check all fields in config are non-empty
        # ConfigParser interprets 'foo=' as mapping foo to the empty string
        for section in config.sections():
            for field in config[section]:
                value = config[section][field]
                if value=='':
                    msg = "[{0}] field '{1}' cannot be an empty string".format(section, field)
                    self.logger.error(msg)
                    raise DjerbaConfigError(msg)
                elif re.search('^[\'"]', value) or re.search('[\'"]$', value):
                    msg = "[{0}] field '{1}' value '{2}' ".format(section, field, value)+\
                          "is a quoted string; may be unable to resolve as a path"
                    self.logger.warning(msg)
        return True

    def validate_full(self, config):
        """Config has all parameters; valid input for extract step"""
        valid = self.validate(config, [ini.INPUTS, ini.SETTINGS, ini.DISCOVERED])
        self.find_extras(config)
        self.logger.info("Successfully validated fully-specified Djerba config")
        return valid

    def validate_minimal(self, config):
        """Config has minimal required parameters; valid input for configure step"""
        valid = self.validate(config, [ini.INPUTS])
        self.find_extras(config)
        self.logger.info("Successfully validated minimal Djerba config")
        return valid

class config_plugin_validator(config_validator):
    """Check that plugin INI parameters are valid"""

    def __init__(self, core_schema, plugin_name, required, optional,
                 log_level=logging.WARNING, log_path=None):
        # core_schema = dictionary representation of config
        # required = list of required fields for plugin
        # optional = list of optional fields for plugin
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.minimal_schema = core_schema.copy()
        self.minimal_schema[plugin_name] = required
        self.full_schema = core_schema.copy()
        self.full_schema[plugin_name] = required+optional
        self.schema = self.full_schema # for methods of parent class
        self.plugin_name = plugin_name

    def validate(self, config, schema):
        for title in schema.keys():
            # ConfigParser throws an error if the same title is specified more than once
            if not title in config.sections():
                msg = "[{0}] section not found in config".format(title)
                self.logger.error(msg)
                raise DjerbaConfigError(msg)
            for field in schema[title]:
                if not config[title].get(field):
                    msg = "[{0}] field '{1}' not found in config".format(title, field)
                    self.logger.error(msg)
                    raise DjerbaConfigError(msg)
        return True

    def validate_full(self, config):
        """Config has all parameters; valid input for extract step"""
        valid = self.validate(config, self.full_schema)
        self.find_extras(config)
        self.logger.info("Full config for plugin {0} is valid".format(self.plugin_name))
        return valid

    def validate_minimal(self, config):
        """Config has minimal required parameters; valid input for configure step"""
        valid = self.validate(config, self.minimal_schema)
        self.find_extras(config)
        self.logger.info("Minimal config for plugin {0} is valid".format(self.plugin_name))
        return valid

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
        if not path:
            error = "Input path '%s' is not a valid path value" % path
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

class DjerbaConfigError(Exception):
    pass

