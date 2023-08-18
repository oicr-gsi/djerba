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
import djerba.snv_indel_tools.constants as sic
from djerba.cnv_tools.preprocess import preprocess as preprocess_cnv
from djerba.cnv_tools.extract import data_builder as cnv_data_extractor
import djerba.render.constants as rc
from djerba.sequenza import sequenza_reader

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'cnv_template.html'
    ASSAY = 'WGS'
    SEQTYPE = 'GENOME'
    HAS_EXPRESSION_DATA = False
    
    def configure(self, config):
      config = self.apply_defaults(config)
      #add find purity from sequenza when not from ini
      #sequenza_solution = config[self.identifier]['sequenza_solution']
      return config  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)  
      work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

      tumour_id = config[self.identifier]['tumour_id']
      sequenza_file = config[self.identifier]['sequenza_file']
      sequenza_gamma = int(config[self.identifier]['sequenza_gamma'])
      purity = config[self.identifier]['purity']
      oncotree_code = config[self.identifier]['oncotree_code']

      seg_path = preprocess_cnv(work_dir).preprocess_seg_sequenza(sequenza_file, tumour_id, sequenza_gamma)
      preprocess_cnv(work_dir).run_R_code(seg_path, purity, tumour_id, oncotree_code)
      #add printed purity cutoffs to json
      cna_annotated_path = os.path.join(work_dir, sic.CNA_ANNOTATED)
      results = cnv_data_extractor(work_dir).build_copy_number_variation(self.ASSAY, cna_annotated_path)
      #add PGA to results
      #data[rc.PERCENT_GENOME_ALTERED] = int(round(self.read_fga()*100, 0))
      #add CNV plot to results
      data['results'] = results
      return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
      required = [
            'sequenza_file',
            'sequenza_gamma',
            'tumour_id',
            'purity',
            'oncotree_code'
          ]
      for key in required:
          self.add_ini_required(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
      self.set_priority_defaults(self.PRIORITY)

    def read_fga(self):
        input_path = os.path.join(self.input_dir, self.DATA_SEGMENTS)
        total = 0
        with open(input_path) as input_file:
            for row in csv.DictReader(input_file, delimiter="\t"):
                if abs(float(row['seg.mean'])) >= self.MINIMUM_MAGNITUDE_SEG_MEAN:
                    total += int(row['loc.end']) - int(row['loc.start'])
        # TODO see GCGI-347 for possible updates to genome size
        fga = float(total)/self.GENOME_SIZE
        return fga