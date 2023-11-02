"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import re
import logging

from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    PRIORITY = 2000
    PLUGIN_VERSION = '1.0'
    TEMPLATE_NAME = 'template.html'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        hrd_file = config[self.identifier]['hrd_file']
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)       
        results =  {
                'files': 
                    {'hrd_file': hrd_file},
                'HRD': 'HRD'
            }
        data['results'] = results
        self.workspace.write_json('hbc_results.json', hrd_file)
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        discovered = [
            'hrd_file'
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)
