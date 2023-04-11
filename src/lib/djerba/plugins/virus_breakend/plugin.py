"""
The purpose of this file is to prototype a plugin for VIRUSBreakend.
"""

# IMPORTS
import os
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.virus_breakend.constants as constants
from djerba.plugins.virus_breakend.extract.report_to_json import data_builder 


class main(plugin_base):
  
    TEMPLATE_NAME = 'virus_template.html'

    def configure(self, config_section):
      #config_section[constants.VIRUSBREAKEND_FILE] = '42' <-- IDK
      return config_section

    def extract(self, config_section):
      data = {
          'plugin_name': 'VIRUSBreakend',
          'clinical': True,
          'failed': False,
          'merge_inputs': {},
          'results': data_builder().build_virusbreakend()
      }
      return data

    def render(self, data):
      args = data
      html_dir = os.path.realpath(os.path.join(
          os.path.dirname(__file__),
          'html'
      ))
      report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
      mako_template = report_lookup.get_template(self.TEMPLATE_NAME)
      try:
          html = mako_template.render(**args)
      except Exception as err:
          msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
          self.logger.error(msg)
          raise
      return html    
