"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import re
import logging
import json

from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    PRIORITY = 3000
    PLUGIN_VERSION = '1.0'
    TEMPLATE_NAME = 'template.html'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        captiv8_path = config[self.identifier]['captiv8_path']
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        captiv8_base64 = self.write_captiv8_plot(work_dir, captiv8_path)       
        results =  {
                'files': 
                    {'captiv8_path': captiv8_path},
                'captiv8-score': 8,
                'eligibility': "eligible",
                'captiv8_base64' : captiv8_base64
            }
        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        discovered = [
            'captiv8_path'
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'research')
        self.set_priority_defaults(self.PRIORITY)

    def write_captiv8_plot(self, output_dir, input_file ):
        args = [
            os.path.join(os.path.dirname(__file__),'plot.R'),
            '--dir', output_dir,
            '--input', input_file
        ]
        pwgs_results = subprocess_runner().run(args)
        return(pwgs_results.stdout.split('"')[1])