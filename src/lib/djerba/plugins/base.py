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

    def __init__(self, **kwargs):
        # workspace is an instance of djerba.core.workspace
        super().__init__(**kwargs)
        self.workspace = kwargs['workspace']
        self.json_validator = plugin_json_validator(self.log_level, self.log_path)
        # global defaults for plugins; can override for individual plugin classes
        self.ini_defaults = {
            core_constants.ATTRIBUTES: '',
            core_constants.DEPENDS_CONFIGURE: '',
            core_constants.DEPENDS_EXTRACT: '',
            core_constants.CONFIGURE_PRIORITY: 1000,
            core_constants.EXTRACT_PRIORITY: 1000,
            core_constants.RENDER_PRIORITY: 1000
        }
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

    def get_starting_plugin_data(self, config_wrapper, plugin_version):
        """Create a data structure with empty merge inputs and results"""
        attributes = config_wrapper.get_my_attributes()
        self.check_attributes_known(attributes)
        data = {
            'plugin_name': self.identifier+' plugin',
            'version': plugin_version,
            'priorities': config_wrapper.get_my_priorities(),
            'attributes': config_wrapper.get_my_attributes(),
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
        for key in core_constants.PRIORITY_KEYS:
            self.ini_defaults[key] = priority

    def update_wrapper_if_null(self, wrapper, file_name, config_key, json_key=None):
        """If parameter is null, attempt to read from workspace JSON"""
        if json_key == None:
            json_key = config_key
        if wrapper.my_param_is_null(config_key):
            if self.workspace.has_file(file_name):
                data = self.workspace.read_json(file_name)
                try:
                    value = data[json_key]
                except KeyError as err:
                    msg = "Cannot find {0} in workspace file {1}".format(json_key, file_name)
                    self.logger.error(msg)
                    raise DjerbaPluginError(msg) from err
                wrapper.set_my_param(config_key, value)
            else:
                msg = "Cannot find {0}; must be manually specified ".format(config_key)+\
                    "or given in workspace {0}".format(file_name)
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        return wrapper

class DjerbaPluginError(Exception):
    """General-purpose class for Djerba plugin errors; can subclass if needed"""
    pass
