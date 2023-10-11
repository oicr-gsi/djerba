"""
Plugin to generate the failed report results summary report section

"""

import logging
from time import strftime
import csv
import os
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
from djerba.core.workspace import workspace

class main(plugin_base):

    PRIORITY = 100
    PLUGIN_VERSION = '0.1'
    MAKO_TEMPLATE_NAME = 'failed_report_template.html'
    FAILED_TEMPLATE_FILE = 'failed_template.txt'
    FAILED_FILE = 'failed_file'
    FAILED_TEXT = 'failed_text'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        
        if wrapper.my_param_is_null(self.FAILED_FILE):
            failed_template_path = os.path.join(os.path.dirname(__file__), self.FAILED_TEMPLATE_FILE) 
            wrapper.set_my_param(self.FAILED_FILE, failed_template_path)

        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        failed_text = self.read_failed_text(config[self.identifier][self.FAILED_FILE])
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS][self.FAILED_TEXT] = failed_text
        self.workspace.write_string('results_summary.txt', failed_text)
        return data

    def specify_params(self):
        discovered = [
            self.FAILED_FILE,
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

    def read_failed_text(self, results_failed_path):
        """
        read results summary from file
        """
        with open(results_failed_path, 'r') as failed_file:
            failed_text = csv.reader(failed_file, delimiter="\t")
            text = ''
            for row in failed_text:
                text = text.join(row)
        return text
