"""
Abstract base class for plugins
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
import re
from abc import ABC
from djerba.core.configure import configurable
from djerba.core.json_validator import plugin_json_validator
import djerba.core.constants as core_constants

class plugin_base(configurable, ABC):

    PRIORITY_KEYS = [
        core_constants.CONFIGURE_PRIORITY,
        core_constants.EXTRACT_PRIORITY,
        core_constants.RENDER_PRIORITY
    ]

    def __init__(self, **kwargs):
        # workspace is an instance of djerba.core.workspace
        super().__init__(**kwargs)
        self.workspace = kwargs['workspace']
        self.json_validator = plugin_json_validator(self.log_level, self.log_path)
        self.specify_params()

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

    def set_priority_defaults(self, priority):
        for key in self.PRIORITY_KEYS:
            self.ini_defaults[key] = priority
