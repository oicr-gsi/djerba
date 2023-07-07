"""Simple Djerba plugin for demonstration and testing: Example 2"""

import logging
from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 800
    PLUGIN_VERSION = '1.0.0'

    # __init__ inherited from parent class

    def configure(self, config):
        config = self.apply_defaults(config)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = {
            'plugin_name': self.identifier+' plugin',
            'version': self.PLUGIN_VERSION,
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {},
            'results': {
                'salutation': 'So long and thanks for all the fish!'
            }
        }
        return data

    def render(self, data):
        return "<h1>Farewell! {0}</h1>".format(data['results']['salutation']),

    def specify_params(self):
        self.logger.debug("Specifying params for plugin demo2")
        self.add_ini_required('salutation')
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)
        self.set_priority_defaults(self.PRIORITY)
