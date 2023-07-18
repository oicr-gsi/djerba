"""
The purpose of this file is to prototype a plugin for TAR SNV Indel
"""

# IMPORTS
import os
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.snv_indel.constants as constants
from djerba.plugins.snv_indel.preprocess import preprocess
from djerba.plugins.snv_indel.extract import data_builder 
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
from djerba.core.workspace import workspace

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'snv_indel_template.html'
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
         
    def specify_params(self):

      self.add_ini_required('maf_file')
      self.add_ini_required('oncotree_code')
      self.add_ini_required('tcgacode')
      self.add_ini_required('gep_file')
      self.add_ini_required('sequenza_file')
      self.add_ini_required('sequenza_gamma')
      self.add_ini_required('sequenza_solution')
      self.add_ini_required('tumour_id')


      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)
      self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):
      config = self.apply_defaults(config)
      return config  

    def extract(self, config):
      
      wrapper = self.get_config_wrapper(config)  
      work_dir = self.workspace.get_work_dir()
      
      # Preprocess the files
      preprocess(config, work_dir, tar = False).run_R_code()

      data = {
          'plugin_name': 'Tar SNV Indel',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': data_builder(work_dir, tar=False).build_small_mutations_and_indels()
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
