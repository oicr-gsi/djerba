"""
Plugin to generate the Results Summary report section

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

    PRIORITY = 400
    PLUGIN_VERSION = '0.1'
    MAKO_TEMPLATE_NAME = 'summary_report_template.html'
    SUMMARY_TEMPLATE_FILE = 'summary_template.txt'
    SUMMARY_FILE = 'summary_file'
    SUMMARY_TEXT = 'summary_text'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        if wrapper.my_param_is_null(self.SUMMARY_FILE):
            summary_template_path = os.path.join(os.path.dirname(__file__), self.SUMMARY_TEMPLATE_FILE) 
            wrapper.set_my_param(self.SUMMARY_FILE, summary_template_path)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        summary_text = self.read_results_summary(config[self.identifier][self.SUMMARY_FILE])
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS][self.SUMMARY_TEXT] = summary_text
        self.workspace.write_string('results_summary.txt', summary_text)
        return data

    def specify_params(self):
        discovered = [
            self.SUMMARY_FILE
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

    def read_results_summary(self, results_summary_path):
        """
        read results summary from file
        """
        with open(results_summary_path, 'r') as summary_file:
            summary_text = csv.reader(summary_file, delimiter="\t")
            summary = ''
            for row in summary_text:
                summary = summary.join(row)
        return summary
