"""
Abstract base class for plugins
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
import re
from abc import ABC
from djerba.core.configurable import configurable
from djerba.core.json_validator import plugin_json_validator
import djerba.core.constants as core_constants

class plugin_base(configurable, ABC):

    def __init__(self, workspace, identifier, log_level=logging.INFO, log_path=None):
        # workspace is an instance of djerba.core.workspace
        super().__init__(identifier, log_level, log_path)
        self.workspace = workspace
        self.json_validator = plugin_json_validator(log_level, log_path)
        defaults = {
            core_constants.CONFIGURE_PRIORITY: self.DEFAULT_CONFIG_PRIORITY,
            core_constants.EXTRACT_PRIORITY: self.DEFAULT_CONFIG_PRIORITY,
            core_constants.RENDER_PRIORITY: self.DEFAULT_CONFIG_PRIORITY
        }
        self.set_all_ini_defaults(defaults)

    # configure() method is defined in parent class

    def extract(self, config):
        """
        Input is a ConfigParser object
        Output is a data structure satisfying the plugin schema
        """
        msg = "Using placeholder method of parent class; returns empty data structure"
        self.logger.debug(msg)
        data = {
            'plugin_name': 'abstract plugin',
            'clinical': True,
            'failed': False,
            'merge_inputs': {},
            'results': {},
        }
        return data

    def render(self, data):
        """
        Input is a data structure satisfying the plugin schema
        Output is a string (for inclusion in an HTML document)
        """
        msg = "Using method of parent class; checks inputs and returns empty string"
        self.logger.debug(msg)
        self.json_validator.validate_data(data)
        return ''
