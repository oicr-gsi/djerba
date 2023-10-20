"""Minimal plugin to generate the supplementary section header"""

import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 1000
    MAKO_TEMPLATE_NAME = 'header.html'
    PLUGIN_VERSION = '1.0.0'
    
    def specify_params(self):
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.DEFAULT_CONFIG_PRIORITY)
    
    def configure(self, config):
        config = self.apply_defaults(config)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
