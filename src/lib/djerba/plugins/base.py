"""
Abstract base class for plugins
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
from abc import ABC
from djerba.core.json_validator import plugin_json_validator
from djerba.util.logger import logger

class plugin_base(logger, ABC):

    def __init__(self, workspace, log_level=logging.INFO, log_path=None):
        # workspace is an instance of djerba.core.workspace
        self.workspace = workspace
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.json_validator = plugin_json_validator(log_level, log_path)
        self.logger.debug("Using constructor of parent class")

    def configure(self, config_section):
        """Input/output is a config section from a ConfigParser object"""
        self.logger.debug("Using method of parent class; returns unchanged config")
        return config_section

    def extract(self, config_section):
        """
        Input is a config section from a ConfigParser object
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
