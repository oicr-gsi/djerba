"""
Plugin to generate the Results Summary report section

"""

import logging
from time import strftime
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '0.1'
    MAKO_TEMPLATE_NAME = 'summary_report_template.html'
    SUMMARY_TEMPLATE_FILE = 'summary_template.txt'
    SUMMARY_TEXT = 'summary_text'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        # populate results directly from config
        results_keys = [
            self.SUMMARY_TEXT
        ]
        results = {k: wrapper.get_my_string(k) for k in results_keys}
        data[core_constants.RESULTS] = results
        return data

    def specify_params(self):
        discovered = [
            self.SUMMARY_TEXT
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

