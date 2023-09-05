"""
a plugin for WGTS SNV Indel
"""

# IMPORTS
import os
import csv
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
from djerba.core.workspace import workspace
import djerba.plugins.wgts.snv_indel_tools.constants as sic
from djerba.plugins.wgts.cnv_tools.preprocess import preprocess as process_cnv
import djerba.render.constants as rc
import djerba.plugins.wgts.cnv_tools.constants as ctc 
from djerba.sequenza import sequenza_reader
from djerba.plugins.wgts.snv_indel_tools.extract import data_builder as data_extractor

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'cnv_template.html'
    ASSAY = 'WGS'
    
    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      if wrapper.my_param_is_null('purity'):
            purity = sequenza_reader(config[self.identifier]['sequenza_file']).get_purity(gamma=int(config[self.identifier]['sequenza_gamma']), solution=config[self.identifier]['sequenza_solution'])
            wrapper.set_my_param('purity', purity)
      #TODO: pull sequenza from provenance
      return config  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)  
      work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
      cnv = process_cnv(work_dir)

      tumour_id = config[self.identifier]['tumour_id']
      sequenza_file = config[self.identifier]['sequenza_file']
      sequenza_gamma = int(config[self.identifier]['sequenza_gamma'])
      sequenza_solution = config[self.identifier]['sequenza_solution']
      purity = config[self.identifier]['purity']
      oncotree_code = config[self.identifier]['oncotree_code']

      seg_path = cnv.preprocess_seg_sequenza(sequenza_file, sequenza_gamma, tumour_id)
      ## outputs files write to working directory
      cnv.convert_to_gene_and_annotate(seg_path, purity, tumour_id, oncotree_code)
      data_table = cnv.build_copy_number_variation(self.ASSAY, sic.CNA_ANNOTATED)
      data_table[ctc.PERCENT_GENOME_ALTERED] = cnv.calculate_percent_genome_altered(ctc.DATA_SEGMENTS)
      if self.ASSAY == "WGS":
        data_table[sic.HAS_EXPRESSION_DATA]= False
      elif self.ASSAY == "WGTS":
        data_table[sic.HAS_EXPRESSION_DATA]= True
        #TODO: add expression support
      cnv_plot_base64 = cnv.write_cnv_plot(sequenza_file, sequenza_gamma, sequenza_solution)
      data_table['cnv_plot']= cnv_plot_base64
      data['results'] = data_table
      cna_annotated_path = os.path.join(work_dir, sic.CNA_ANNOTATED)
      data['merge_inputs']['treatment_options_merger'] =  cnv.build_therapy_info(cna_annotated_path, oncotree_code)
      return data
    
    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
      required = [
            'sequenza_file',
            'sequenza_gamma',
            'sequenza_solution',
            'tumour_id',
            'oncotree_code'
          ]
      for key in required:
          self.add_ini_required(key)
      discovered = [
            'purity'
        ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
      self.set_priority_defaults(self.PRIORITY)