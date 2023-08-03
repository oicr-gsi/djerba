"""
Plugin for TAR SNV Indel
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
import djerba.plugins.tar.provenance_tools as provenance_tools
from djerba.core.workspace import workspace

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'snv_indel_template.html'
    WORKFLOW = 'consensusCruncher'
    RESULTS_SUFFIX_Pl = 'Pl.merged.maf.gz'
    RESULTS_SUFFIX_BC = 'BC.merged.maf.gz'
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
         
    def specify_params(self):
      self.add_ini_required('maf_file')
      self.add_ini_required('maf_file_normal')
      self.add_ini_required('oncotree_code')
      self.add_ini_required('tcgacode')
      self.add_ini_required('tumour_id')

      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)
      self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):
      config = self.apply_defaults(config)

      # Populate ini
      config[self.identifier]["maf_file"] = self.get_maf_file(config["tar.sample"]["root_sample_name"], self.RESULTS_SUFFIX_Pl)
      config[self.identifier]["maf_file_normal"] = self.get_maf_file(config["tar.sample"]["root_sample_name"], self.RESULTS_SUFFIX_BC)
      
      return config  

    def extract(self, config):
      
      wrapper = self.get_config_wrapper(config)  
      # Pre-process all the files
      # self.preprocess()
      work_dir = self.workspace.get_work_dir()
      #work_dir = "."
      #print(work_dir)
      preprocess(config, work_dir, tar=True).run_R_code()

      data = {
          'plugin_name': 'Tar SNV Indel',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': data_builder(work_dir, tar=True).build_small_mutations_and_indels()
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


    def get_maf_file(self, root_sample_name, results_suffix):
      """
      pull data from results file
      """
      provenance = provenance_tools.subset_provenance(self, self.WORKFLOW, root_sample_name)
      try:
          results_path = provenance_tools.parse_file_path(self, results_suffix, provenance)
      except OSError as err:
          msg = "File with extension {0} not found".format(results_suffix)
          raise RuntimeError(msg) from err
      return results_path

