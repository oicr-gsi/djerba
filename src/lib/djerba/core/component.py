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

    def __init__(self, identifier, log_level=logging.INFO, log_path=None):
        self.identifier = identifier
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def configure(self, config):
        """Input/output is a ConfigParser object"""
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
