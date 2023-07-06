"""
Base class for all components: Plugins, helpers, mergers

Defines a wide range of methods for common configuration tasks
"""

import logging
import os
import string
from abc import ABC, abstractmethod
from configparser import ConfigParser
from djerba.util.logger import logger
import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini

class configurable(logger, ABC):

    """
    Interface for Djerba objects configurable by INI
    Subclasses include the core configurer, and all plugin/helper/merger classes

    Implements a number of methods, organized below as follows:
    - General-purpose methods
    - Required/default parameters and parameter validation
    - Get special directory paths from environment variables
    - Handle component priorities
    - Get/set/query INI params (other than priority levels)
    """

    def __init__(self, **kwargs):
        self.identifier = kwargs[core_constants.IDENTIFIER]
        self.module_dir = kwargs[core_constants.MODULE_DIR]
        self.log_level = kwargs[core_constants.LOG_LEVEL]
        self.log_path = kwargs[core_constants.LOG_PATH]
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.ini_required = set() # names of INI parameters the user must supply
        self.ini_defaults = {} # names and default values for other INI parameters

    def _raise_unknown_config_error(self, key, complete=True):
        mode = 'fully-specified' if complete else 'minimal'
        template = "Unknown INI parameter '{0}' in {1} config of component {2}. "+\
            "Required = {3}, Defaults = {4}"
        params = (key, mode, self.identifier, self.ini_required, self.ini_defaults)
        msg = template.format(params)
        self.logger.error(msg)
        raise DjerbaConfigError(msg)

    def _raise_missing_config_error(self, key, input_keys, complete=True):
        mode = 'fully-specified' if complete else 'minimal'
        template = "Key '{0}' required for {1} config "+\
            "of component {2} was not found in inputs {3}"
        msg = template.format(key, mode, self.identifier, input_keys)
        self.logger.error(msg)
        raise DjerbaConfigError(msg)

    def configure(self, config):
        """Input/output is a ConfigParser object"""
        self.logger.debug("Superclass configure method; only applies defaults (if any)")
        config = self.apply_defaults(config)
        return config

    def get_config_wrapper(self, config):
        return config_wrapper(config, self.identifier, self.log_level, self.log_path)

    def get_default_config_priority(self):
        # configure priority is defined for all component types: plugin, helper, merger
        return self.ini_defaults[core_constants.CONFIGURE_PRIORITY]

    def get_default_dependencies(self):
        # return default dependencies -- if any, None otherwise
        return self.ini_defaults.get(core_constants.DEPENDS)

    def get_module_dir(self):
        return self.module_dir

    def set_log_level(self, level):
        # use to change the log level set by the component loader, eg. for testing
        self.logger.setLevel(level)

    @abstractmethod
    def specify_params(self):
        self.logger.warning("Abstract specify_params not intended to be called")

    #################################################################
    ### start of methods to handle required/default parameters

    def add_ini_required(self, key):
        self.ini_required.add(key)

    def apply_defaults(self, config):
        """
        Apply default parameters to the given ConfigParser
        This method does not overwrite existing values
        """
        for key in self.ini_defaults:
            if not config.has_option(self.identifier, key):
                config.set(self.identifier, key, str(self.ini_defaults[key]))
        return config

    def get_all_expected_ini(self):
        # returns a set of all expected INI parameter names
        return self.ini_required.union(set(self.ini_defaults.keys()))

    def get_expected_config(self):
        """
        Return a ConfigParser with all expected params
        Params are set to their default values, if any; None otherwise
        Template substitution is *not* done here
        Can use to generate a config file for manual completion
        """
        config = ConfigParser()
        config.add_section(self.identifier)
        self.specify_params()
        for option in sorted(list(self.ini_required)):
            config.set(self.identifier, option, 'REQUIRED')
        for option in sorted(list(self.ini_defaults.keys())):
            config.set(self.identifier, option, str(self.ini_defaults[option]))
        return config

    def set_ini_default(self, key, value):
        self.ini_defaults[key] = value

    @abstractmethod
    def set_priority_defaults(self, priority):
        # convenience method to set all priority defaults to the given value
        # which priorities are defined depends if plugin, helper, or merger
        self.logger.warning("Abstract set_priority_defaults not intended to be called")

    def validate_minimal_config(self, config):
        """Check for required/unknown config keys in minimal config"""
        self.logger.info("Validating minimal config for component "+self.identifier)
        input_keys = config.options(self.identifier)
        for key in self.ini_required:
            if key not in input_keys:
                self._raise_missing_config_error(key, input_keys, complete=False)
        for key in input_keys:
            if key not in self.ini_required and key not in self.ini_defaults:
                self._raise_unknown_config_error(key, complete=False)
        self.validate_priorities(config)
        return True

    def validate_full_config(self, config):
        """Check that all config keys (both required and optional) are present"""
        # TODO check that all reserved keys are present
        self.logger.info("Validating fully-specified config for component "+self.identifier)
        all_keys = self.get_all_expected_ini()
        template = "{0} expected INI param(s) found for component {1}"
        self.logger.debug(template.format(len(all_keys), self.identifier))
        input_keys = config.options(self.identifier)
        for key in all_keys:
            if key not in input_keys:
                self._raise_missing_config_error(key, input_keys, complete=True)
        for key in input_keys:
            if key not in all_keys:
                self._raise_unknown_config_error(key, complete=True)
        self.validate_priorities(config)
        return True

    def validate_priorities(self, config):
        # check priorities are non-negative integers
        # TODO sanity checking on other reserved params
        ok = True
        for s in config.sections():
            for p in core_constants.PRIORITY_KEYS:
                if config.has_option(s, p):
                    try:
                        v = config.getint(s, p)
                    except ValueError:
                        ok = False
                    if v < 0:
                        ok = False
                if not ok:
                    msg = "{0}:{1} must be a non-negative integer; got {2}".format(s, p, v)
                    self.logger.error(msg)
                    raise ValueError(msg)

    ### end of methods to handle required/default parameters
    ### start of methods to handle component priorities

class configurer(configurable):

    """Class to do core configuration"""

    PRIORITY = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.specify_params()

    def configure(self, config):
        config = self.apply_defaults(config)
        config.set(ini.CORE, 'comment', 'Djerba 1.0 under development')
        return config

    def set_priority_defaults(self, priority):
        for key in core_constants.PRIORITY_KEYS:
            self.ini_defaults[key] = priority

    def specify_params(self):
        self.set_priority_defaults(self.PRIORITY)
        self.set_ini_default('comment', 'comment goes here')


class config_wrapper(logger):

    """Wrapper for a ConfigParser object with convenience methods"""

    def __init__(self, config, identifier, log_level=logging.WARNING, log_path=None):
        # config is a ConfigParser object
        # identifier is the component identifier, used to retrieve INI params
        self.config = config
        self.identifier = identifier
        self.logger = self.get_logger(log_level, __name__, log_path)

    def get_config(self):
        return self.config

    #################################################################
    ### start of methods to get/set/query INI params (other than priority levels)

    def get_core_string(self, param):
        return self.config.get(ini.CORE, param)

    def get_core_int(self, param):
        return self.config.getint(ini.CORE, param)

    def get_core_float(self, param):
        return self.config.getfloat(ini.CORE, param)

    def get_core_boolean(self, param):
        return self.config.getboolean(ini.CORE, param)

    # no set_core_param() -- components only write their own INI section

    def get_my_attributes(self):
        attributes = []
        for key in ['clinical', 'supplementary', 'failed']:
            if self.config.has_option(self.identifier, key) \
               and self.config.getboolean(self.identifier, key):
                attributes.append(key)
        return attributes

    # [get|set|has]_my_* methods for the named component

    def get_my_boolean(self, param):
        return self.config.getboolean(self.identifier, param)

    def get_my_float(self, param):
        return self.config.getfloat(self.identifier, param)

    def get_my_int(self, param):
        return self.config.getint(self.identifier, param)

    def get_my_string(self, param):
        return self.config.get(self.identifier, param)

    def has_my_param(self, param):
        return self.config.has_option(self.identifier, param)

    def get_my_priorities(self):
        """
        Find configure/extract/render priorities, if any
        extract and render are not defined for mergers and helpers, respectively
        Used at extract step to convert INI settings into JSON
        """
        priorities = {}
        mapping = {
            core_constants.CONFIGURE_PRIORITY: core_constants.CONFIGURE,
            core_constants.EXTRACT_PRIORITY: core_constants.EXTRACT,
            core_constants.RENDER_PRIORITY: core_constants.RENDER
        }
        for key, value in mapping.items():
            if self.config.has_option(self.identifier, key):
                priorities[value] = self.config.getint(self.identifier, key)
        return priorities

    def set_my_priorities(self, priority):
        # convenience method; sets all defined priorities to the same value
        for key in core_constants.PRIORITY_KEYS:
            if self.has_my_param(key):
                self.set_my_param(key, priority)

    def set_my_param(self, param, value):
        self.config.set(self.identifier, param, str(value))

    # [get|set|has]_my_* methods for other components

    def get_boolean(self, section, param):
        return self.config.getboolean(section, param)

    def get_float(self, section, param):
        return self.config.getfloat(section, param)

    def get_int(self, section, param):
        return self.config.getint(section, param)

    def get(self, section, param):
        # alias for get_string, to be consistent with ConfigParser interface
        return self.get_string(section, param)

    def get_string(self, section, param):
        return self.config.get(section, param)

    def has_option(self, section, param):
        # alias for has_param, to be consistent with ConfigParser interface
        return self.has_param(section, param)

    def has_param(self, section, param):
        return self.config.has_option(section, param)

    def set_param(self, section, param, value):
        self.config.set(section, param, str(value))

    def set(self, section, param, value):
        # alias for set_param, to be consistent with ConfigParser interface
        self.set_param(section, param, value)

    ### end of methods to get/set/query INI params (other than priority levels)
    #################################################################
    ### start of methods to get special directory paths from environment variables

    def apply_env_templates(self, section):
        """
        Included for completeness -- but normally we will use apply_my_env_templates()

        Apply template substitution using variables
        Replace strings like $DJERBA_DATA_DIR with value of corresponding env variable
        https://docs.python.org/3/library/string.html#string.Template.substitute
        """
        var_names = [
            core_constants.DJERBA_DATA_DIR_VAR,
            core_constants.DJERBA_PRIVATE_DIR_VAR,
            core_constants.DJERBA_TEST_DIR_VAR
        ]
        mapping = {var: self.get_dir_from_env(var) for var in var_names}
        for section in self.config.sections():
            for option in self.config.options(section):
                value = self.config.get(section, option)
                try:
                    value = string.Template(value).substitute(mapping)
                except KeyError as err:
                    msg = "Failed to substitute environment variable in INI "+\
                        "section {0}, option {1}, value {2}".format(section, option, value)+\
                        ": {0}".format(err)
                    self.logger.error(msg)
                    raise DjerbaConfigError(msg) from err
                self.config.set(section, option, value)

    def apply_my_env_templates(self):
        self.apply_env_templates(self.identifier)

    def get_dir_from_env(self, var):
        dir_path = os.environ.get(var)
        if dir_path == None:
            msg = "Environment variable '{0}' is not configured".format(var)
            self.logger.warning(msg)
        return dir_path

    def get_djerba_data_dir(self):
        return self.get_dir_from_env(core_constants.DJERBA_DATA_DIR_VAR)

    def get_djerba_private_dir(self):
        return self.get_dir_from_env(core_constants.DJERBA_PRIVATE_DIR_VAR)

    def get_djerba_test_dir(self):
        return self.get_dir_from_env(core_constants.DJERBA_TEST_DIR_VAR)

    ### end of methods to get special directory paths from environment variables
    #################################################################


class DjerbaConfigError(Exception):
    pass
