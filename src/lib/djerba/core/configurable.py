"""
Base class for all components: Plugins, helpers, mergers

Defines several 'get_my_*' convenience methods to get component INI params
"""

import logging
import os
import string
from abc import ABC
from djerba.util.logger import logger
import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini

class configurable(logger, ABC):

    """
    Interface for Djerba objects configurable by INI
    Subclasses include the core configurer, and all plugin/helper/merger classes
    Has methods to get/set/validate config parameters, requirements, and defaults
    """

    DEFAULT_CONFIG_PRIORITY = 10000 # override in subclasses

    def __init__(self, identifier, log_level=logging.INFO, log_path=None):
        self.identifier = identifier
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.ini_required = set() # names of INI parameters the user must supply
        self.ini_defaults = {} # names and default values for other INI parameters

    def _log_unknown_config_warning(self, key, complete=True):
        mode = 'fully-specified' if complete else 'minimal'
        template = "Unknown INI parameter '{0}' in {1} config of component {2}"
        self.logger.warning(template.format(key, mode, self.identifier))

    def _raise_config_error(self, key, input_keys, complete=True):
        mode = 'fully-specified' if complete else 'minimal'
        template = "Key '{0}' required for {1} config "+\
            "of component {2} was not found in inputs {3}"
        msg = template.format(key, mode, self.identifier, input_keys)
        self.logger.error(msg)
        raise DjerbaConfigError(msg)

    def apply_defaults(self, config):
        """Apply default parameters to the given config, with template substitution"""
        for key in self.ini_defaults:
            if not config.has_option(self.identifier, key):
                config.set(self.identifier, key, str(self.ini_defaults[key]))
        config = self.apply_template_substitution(config)
        return config

    def apply_template_substitution(self, config, section=None):
        """
        Apply template substitution to the given config
        Used automatically when applying defaults
        Automatic usage will do template substution to all parameters, default or manual
        Can also be called manually if needed
        If section name is given, only apply to the named section; otherwise, all sections
        Uses 'safe substitution' of templates, see:
        https://docs.python.org/3/library/string.html#string.Template.safe_substitute
        """
        if section:
            sections = [section, ]
        else:
            sections = config.sections()
        var_names = [
            core_constants.DJERBA_DATA_DIR_VAR,
            core_constants.DJERBA_PRIVATE_DIR_VAR,
            core_constants.DJERBA_TEST_DIR_VAR
        ]
        mapping = {var: os.environ.get(var) for var in var_names} # values may be None
        for section in sections:
            for option in config.options(section):
                value = config.get(section, option)
                value = string.Template(value).safe_substitute(mapping)
                config.set(section, option, value)
        return config

    def configure(self, config):
        """Input/output is a ConfigParser object"""
        self.logger.debug("Superclass configure method; only applies defaults (if any)")
        config = self.apply_defaults(config)
        return config

    def get_all_expected_ini(self):
        # returns a set of all expected INI parameter names
        return self.ini_required.union(set(self.ini_defaults.keys()))

    ### start of methods to get values from environment variables

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

    ### end of methods to get values from environment variables

    def get_default_config_priority(self):
        return self.DEFAULT_CONFIG_PRIORITY

    def get_core_param_string(self, config, param):
        return config.get(ini.CORE, param)

    # set_core_param method intentionally omitted
    # components should not normally set core params

    def get_my_attributes(self, config):
        attributes = []
        for key in ['clinical', 'supplementary', 'failed']:
            if config.has_option(self.identifier, key) \
               and config.getboolean(self.identifier, key):
                attributes.append(key)
        return attributes

    def get_my_param_boolean(self, config, param):
        return config.getboolean(self.identifier, param)

    def get_my_param_float(self, config, param):
        return config.getfloat(self.identifier, param)

    def get_my_param_int(self, config, param):
        return config.getint(self.identifier, param)

    def get_my_param_string(self, config, param):
        return config.get(self.identifier, param)

    def get_my_priorities(self, config):
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
            if config.has_option(self.identifier, key):
                priorities[value] = config.getint(self.identifier, key)
        return priorities

    def get_template_config(self):
        # TODO generate a template ConfigParser with defaults
        # can output as a file for manual editing
        raise RuntimeError('template config not yet available!')

    def has_my_param(self, config, param):
        return config.has_option(self.identifier, param)

    def set_all_priorities(self, config, priority):
        # convenience method; sets all defined priorities to the same value
        all_params = self.get_all_expected_ini()
        priority_keys = [
            core_constants.CONFIGURE_PRIORITY,
            core_constants.EXTRACT_PRIORITY,
            core_constants.RENDER_PRIORITY
        ]
        for key in priority_keys:
            if key in all_params:
                config = self.set_my_param(config, key, priority)
        return config

    def set_my_param(self, config, param, value):
        config.set(self.identifier, param, str(value))
        return config

    ### start of add/set methods for expected params
    # optional parameters have defaults; required parameters do not

    def add_ini_required(self, key):
        self.ini_required.add(key)

    def set_all_ini_defaults(self, mapping):
        # overwrites all existing defaults with the given mapping
        self.ini_defaults = mapping

    def set_all_ini_required(self, required):
        # overwrites all existing requirements with the given input
        # input may be any iterable, eg. a list or set
        self.ini_required = set(required)

    def set_ini_default(self, key, value):
        self.ini_defaults[key] = value

    ### end of add/set expected INI methods

    def set_log_level(self, level):
        # use to change the log level set by the component loader, eg. for testing
        self.logger.setLevel(level)

    def validate_minimal_config(self, config):
        """Check for required/unknown config keys in minimal config"""
        self.logger.info("Validating minimal config for component "+self.identifier)
        input_keys = config.options(self.identifier)
        for key in self.ini_required:
            if key not in input_keys:
                self._raise_config_error(key, input_keys, complete=False)
        for key in input_keys:
            if key not in self.ini_required and key not in self.ini_defaults:
                self._log_unknown_config_warning(key, complete=False)
        return True

    def validate_full_config(self, config):
        """Check that all config keys (both required and optional) are present"""
        self.logger.info("Validating fully-specified config for component "+self.identifier)
        all_keys = self.get_all_expected_ini()
        template = "{0} expected INI param(s) found for component {1}"
        self.logger.debug(template.format(len(all_keys), self.identifier))
        input_keys = config.options(self.identifier)
        for key in all_keys:
            if key not in input_keys:
                self._raise_config_error(key, input_keys, complete=True)
        for key in input_keys:
            if key not in all_keys:
                self._log_unknown_config_warning(key, complete=True)
        return True

class DjerbaConfigError(Exception):
    pass
