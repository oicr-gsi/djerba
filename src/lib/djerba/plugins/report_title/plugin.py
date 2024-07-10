
import logging
from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    PRIORITY = 10
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'title.html'

    # __init__ is inherited from the parent class

    def configure(self, config):
        config = self.apply_defaults(config)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        attributes = wrapper.get_my_attributes()
        self.check_attributes_known(attributes)
        data = {
            'plugin_name': self.identifier+' plugin',
            'version': self.PLUGIN_VERSION,
            'priorities': wrapper.get_my_priorities(),
            'attributes': attributes,
            'merge_inputs': {}
        }
        
        failed = wrapper.get_my_boolean('failed')

        if failed == True:
            data['results'] = {'header_type': 'failed_title'}
        elif failed == False:
            data['results'] = {'header_type': 'clinical_title'}
        return data

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)

    def specify_params(self):
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default("failed", False)
        self.set_priority_defaults(self.PRIORITY)
