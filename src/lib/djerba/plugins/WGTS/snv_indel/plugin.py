"""
The purpose of this file is to prototype a plugin for TAR SNV Indel
"""

# IMPORTS
import os
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.snv_indel_tools.constants as constants
from djerba.snv_indel_tools.preprocess import preprocess
from djerba.snv_indel_tools.extract import data_builder as data_extractor
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
from djerba.core.workspace import workspace
from djerba.util.render_mako import mako_renderer
import djerba.snv_indel_tools.constants as sic

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'snv_indel_template.html'
    
    def configure(self, config):
      config = self.apply_defaults(config)
      return config  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)  
      work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

      preprocess(config, work_dir, tar = False).run_R_code()
      mutations_file = os.path.join(self.work_dir, sic.MUTATIONS_EXTENDED)
      mutations_extended_file = os.path.join(self.work_dir, sic.MUTATIONS_EXTENDED_ONCOGENIC)
      data = data_extractor(assay = assay).build_small_mutations_and_indels(mutations_extended_file)
      results = {
           sic.VAF_PLOT: data_extractor(assay, oncotree).write_vaf_plot(self.work_dir),
           sic.CLINICALLY_RELEVANT_VARIANTS: len(data),
           sic.TOTAL_VARIANTS: data_extractor(assay, oncotree).read_somatic_mutation_totals(mutations_file),
           sic.BODY: data
      }
      data['results'] = results
      return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
      required = [
            'maf_file',
            'oncotree_code',
            'tcgacode',
            'sequenza_file',
            'sequenza_gamma',
            'sequenza_solution'
            'tumour_id',
            'normal_id',
            'study_title'
        ]
      for key in required:
          self.add_ini_required(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
      self.set_priority_defaults(self.PRIORITY)
