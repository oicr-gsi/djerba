"""
Abstract base class for plugins
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
import re
from abc import ABC
from djerba.core.json_validator import plugin_json_validator
from djerba.util.logger import logger
import djerba.core.constants as core_constants

class plugin_base(logger, ABC):

    def __init__(self, workspace, log_level=logging.INFO, log_path=None):
        # workspace is an instance of djerba.core.workspace
        self.workspace = workspace
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.json_validator = plugin_json_validator(log_level, log_path)
        self.logger.debug("Using constructor of parent class")

    def _get_attributes(self, config_section):
        attributes = []
        for key in ['clinical', 'supplementary']:
            if config_section[key]=='true': # TODO FIXME better Boolean check
                attributes.append(key)
        return attributes

    def _get_name(self, name_attr):
        # TODO FIXME tidy this up and define variables for strings
        terms = re.split('\.', name_attr)
        keep = [x for x in terms if x not in ['djerba', 'plugins', 'plugin']]
        return '.'.join(keep)

    def _get_priorities(self, config_section):
        priorities = {
            'configure': int(config_section[core_constants.CONFIGURE_PRIORITY]),
            'extract': int(config_section[core_constants.EXTRACT_PRIORITY]),
            'render': int(config_section[core_constants.RENDER_PRIORITY])
        }
        return priorities

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
