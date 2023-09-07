"""Djerba plugin for pwgs supplement"""
import logging
import os
from djerba.plugins.base import plugin_base, DjerbaPluginError
import djerba.core.constants as core_constants
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 1000
    MAKO_TEMPLATE_NAME = 'supplementary_materials_template.html'
    SUPPLEMENT_DJERBA_VERSION = 0.1
    INPUT_PARAMS_FILE = "input_params.json"
    ASSAY = "assay"
    
    def specify_params(self):
        discovered = [
            self.ASSAY
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_priorities(self.DEFAULT_CONFIG_PRIORITY)
        
        # If input_params.json exists, read it
        work_dir = self.workspace.get_work_dir()
        input_data_path = os.path.join(work_dir, self.INPUT_PARAMS_FILE)
        if os.path.exists(input_data_path):
            input_data = self.workspace.read_json(self.INPUT_PARAMS_FILE)
        else:
            msg = "Could not find input_params.json"
            #print(msg) <-- TO DO: have logger raise warning
        
        if wrapper.my_param_is_null(self.ASSAY):
            wrapper.set_my_param(self.ASSAY, input_data[self.ASSAY])
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
                'assay': config[self.identifier][self.ASSAY]
            },
            'version': str(self.SUPPLEMENT_DJERBA_VERSION)
        }
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)
