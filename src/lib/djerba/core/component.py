"""
Base class for all components: Plugins, helpers, mergers

Defines several 'get_my_*' convenience methods to get component INI params
"""

import logging
from abc import ABC
from djerba.util.logger import logger
import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini

class component(logger, ABC):

    DEFAULT_CONFIG_PRIORITY = 10000 # override in subclasses
    DJERBA_DATA_PUBLIC_VAR = 'DJERBA_DATA_PUBLIC'
    DJERBA_DATA_PRIVATE_VAR = 'DJERBA_DATA_PRIVATE'

    def __init__(self, identifier, log_level=logging.INFO, log_path=None):
        self.identifier = identifier
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.ini_required = set() # names of INI parameters the user must supply
        self.ini_defaults = {} # names and default values for other INI parameters

    def _log_unknown_config_warning(self, key, complete=True):
        mode = 'fully-specified' if complete else 'minimal'
        template = "Unknown INI parameter '{0}' for {1} config of component {2}"
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
                config.set(self.identifier, self.ini_defaults[key])
        return config

    def configure(self, config):
        """Input/output is a ConfigParser object"""
        self.validate_config(config)
        self.logger.debug("Using method of parent class; returns unchanged config")
        return config

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

    def has_my_param(self, config, param):
        return config.has_option(self.identifier, param)

    def set_my_param(self, config, param, value):
        config.set(self.identifier, param, str(value))
        return config

    # optional parameters have defaults; required parameters do not
    # can discover optional default parameters at runtime
    # defaults will be overwritten by manually specified parameters, if given

    def add_ini_required(self, key):
        self.ini_required.add(key)

    def set_all_ini_defaults(self, mapping):
        self.ini_defaults = mapping

    def set_all_ini_required(self, default_set):
        self.ini_required = default_set

    def set_ini_default(self, key, value):
        self.ini_defaults[key] = value

    # end of 'add/set INI' methods

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

    def validate_full_config(self, config):
        """Check that all config keys (both required and optional) are present"""
        self.logger.info("Validating fully-specified config for component "+self.identifier)
        all_keys = self.ini_required.union(set(self.ini_defaults.keys()))
        if len(all_keys)==0:
            msg = "No expected INI params have been specified for "+\
                "component {0}".format(self.identifier)
            self.logger.debug(msg)
        input_keys = config.options(self.identifier)
        for key in all_keys:
            if key not in input_keys:
                self._raise_config_error(key, input_keys, complete=True)
        for key in input_keys:
            if key not in all_keys:
                self._log_unknown_config_warning(key, complete=True)

class DjerbaConfigError(Exception):
    pass
