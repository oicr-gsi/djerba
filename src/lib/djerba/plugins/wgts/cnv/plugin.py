"""
a plugin for WGTS SNV Indel
"""

# IMPORTS
import os
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
from djerba.core.workspace import workspace
import djerba.snv_indel_tools.constants as sic
from djerba.snv_indel_tools.preprocess import preprocess
from djerba.snv_indel_tools.extract import data_builder as data_extractor
import djerba.render.constants as rc

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'snv_indel_template.html'
    ASSAY = 'WGS'
    SEQTYPE = 'GENOME'
    HAS_EXPRESSION_DATA = False
    
    def configure(self, config):
      config = self.apply_defaults(config)
      return config  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)  
      work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
      oncotree = config[self.identifier]['oncotree_code']

      cbioid = config[self.identifier]['study_title']
      tumour_id = config[self.identifier]['tumour_id']
      normal_id = config[self.identifier]['normal_id']
      maf_file = config[self.identifier]['maf_file']
      cna_file = config[self.identifier]['cna_file']

      # gep_file = self.config[self.identifier]['gep_file']

      whizbam_url = preprocess.construct_whizbam_link(sic.WHIZBAM_BASE_URL, cbioid, tumour_id, normal_id, self.SEQTYPE, self.GENOME)

      preprocess(work_dir).run_R_code(whizbam_url, self.ASSAY, maf_file, tumour_id, oncotree)
      data_table = data_extractor(work_dir).build_small_mutations_and_indels(os.path.join(work_dir, sic.MUTATIONS_EXTENDED_ONCOGENIC), cna_file, oncotree, self.ASSAY)
      mutations_file = os.path.join(work_dir, sic.MUTATIONS_EXTENDED)
      results = {
          sic.BODY: data_table,
          sic.CLINICALLY_RELEVANT_VARIANTS: len(data_table),
          sic.TOTAL_VARIANTS: data_extractor(work_dir).read_somatic_mutation_totals(mutations_file),
          rc.HAS_EXPRESSION_DATA: self.HAS_EXPRESSION_DATA,
          sic.VAF_PLOT: data_extractor(work_dir).write_vaf_plot(work_dir)
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
            'tumour_id',
            'normal_id',
            'study_title',
            'cna_file'
        ]
      for key in required:
          self.add_ini_required(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
      self.set_priority_defaults(self.PRIORITY)
