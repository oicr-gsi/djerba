"""
Plugin for whole-genome CNV reporting
"""

import os
import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.sequenza import sequenza_reader # TODO move sequenza.py to util?
from djerba.util.render_mako import mako_renderer

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'cnv_template.html'
    ASSAY = 'WGS'

    # INI param names
    # these params are also used by other plugins; TODO remove reundancy
    SEQUENZA_PATH = 'sequenza_path'
    SEQUENZA_GAMMA = 'sequenza_gamma'
    SEQUENZA_SOLUTION = 'sequenza_solution'
    PURITY = 'purity'
    TUMOUR_ID = 'tumour_id'
    ONCOTREE_CODE = 'oncotree_code'

    # keys for JSON output
    ALTERATION = 'Alteration'
    CHROMOSOME = 'Chromosome'
    EXPRESSION_PERCENTILE = 'Expression Percentile'
    GENE = 'Gene'
    GENE_URL = 'Gene_URL'
    ONCOKB = core_constants.ONCOKB

    # constants for rendering
    PERCENT_GENOME_ALTERED = 'percent_genome_altered'
    TOTAL_VARIANTS = 'total_variants'
    CLINICALLY_RELEVANT_VARIANTS = 'clinically_relevant_variants'
    
    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      # TODO get sequenza path from provenenance helper JSON
      if wrapper.my_param_is_null(self.PURITY):
          gamma = config.get_my_int(self.SEQUENZA_GAMMA)
          solution = config.get_my_string(self.SEQUENZA_SOLUTION)
          reader = sequenza_reader(config.get_my_string(self.SEQUENZA_PATH))
          wrapper.set_my_param(self.PURITY, reader.get_purity(gamma, solution))
      return wrapper.get_config()

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)  
      work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
      cnv = process_cnv(work_dir)

      tumour_id = wrapper.get_my_string(self.TUMOUR_ID)
      sequenza_path = wrapper.get_my_string(self.SEQUENZA_PATH)
      sequenza_gamma = wrapper.get_my_int(self.SEQUENZA_GAMMA)
      sequenza_solution = wrapper.get_my_string(self.SEQUENZA_SOLUTION)
      purity = wrapper.get_my_float(self.PURITY)
      oncotree_code = wrapper.get_my_string(self.ONCOTREE_CODE)

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
      #TODO: add all gene names to merge
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
