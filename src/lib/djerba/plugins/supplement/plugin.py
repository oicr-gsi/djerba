"""Djerba plugin for pwgs supplement"""
import logging

from djerba.plugins.base import plugin_base, DjerbaPluginError
import djerba.core.constants as core_constants
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 1000
    MAKO_TEMPLATE_NAME = 'supplementary_materials_template.html'
    SUPPLEMENT_DJERBA_VERSION = 0.1
    FAILED = "failed"
    ASSAY = "assay"
    
    def specify_params(self):
        required = [
            self.ASSAY
        ]
        for key in required:
            self.add_ini_required(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(self.FAILED, "False")
    
    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_priorities(self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        #TO DO: add a check that assay type is a permitted value
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {},
            'results': {
                'assay': config[self.identifier][self.ASSAY],
                'failed': config[self.identifier][self.FAILED]
            },
            'version': str(self.SUPPLEMENT_DJERBA_VERSION)
        }
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
