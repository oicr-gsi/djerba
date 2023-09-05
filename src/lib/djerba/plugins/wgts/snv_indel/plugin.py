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
import djerba.plugins.wgts.snv_indel_tools.constants as sic
from djerba.plugins.wgts.snv_indel_tools.preprocess import preprocess
from djerba.plugins.wgts.snv_indel_tools.extract import data_builder as data_extractor
import djerba.render.constants as rc

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'snv_indel_template.html'
    ASSAY = 'WGS'
    SEQTYPE = 'GENOME'
    GENOME = 'hg38'
    HAS_EXPRESSION_DATA = False
    
    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      work_dir = self.workspace.get_work_dir()
      if wrapper.my_param_is_null(sic.CNA_FILE):
            wrapper.set_my_param(sic.CNA_FILE, os.path.join(work_dir, sic.CNA_SIMPLE))
      #TODO: pull MAF from provenance
      # group_id = config[self.identifier][pc.GROUP_ID]
      # if wrapper.my_param_is_null(sic.MAF_FILE):
      #       wrapper.set_my_param(sic.MAF_FILE, pwgs_tools.subset_provenance(self, "mrdetect", group_id, pc.RESULTS_SUFFIX))
      #TODO: if cbio_id undefined, set to studyid, but can be entered in ini
      return config  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)  
      work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
      oncotree_code = config[self.identifier]['oncotree_code']
      cbio_id = config[self.identifier]['cbio_id']
      tumour_id = config[self.identifier]['tumour_id']
      normal_id = config[self.identifier]['normal_id']
      maf_file = config[self.identifier]['maf_file']
      cna_file = config[self.identifier]['cna_file']
      #TODO: add expression
      #input_path = os.path.join(work_dir, sic.expr_input)

      whizbam_url = preprocess.construct_whizbam_link(sic.WHIZBAM_BASE_URL, cbio_id, tumour_id, normal_id, self.SEQTYPE, self.GENOME)
      preprocess(work_dir).run_R_code(whizbam_url, self.ASSAY, maf_file, tumour_id, oncotree_code)
      oncogenic_variants_file = os.path.join(work_dir, sic.MUTATIONS_EXTENDED_ONCOGENIC)
      oncogenic_variants_table = data_extractor().build_small_mutations_and_indels(oncogenic_variants_file, cna_file, oncotree_code, self.ASSAY)
      total_variants_file = os.path.join(work_dir, sic.MUTATIONS_EXTENDED)
      results = {
          sic.BODY: oncogenic_variants_table,
          sic.CLINICALLY_RELEVANT_VARIANTS: len(oncogenic_variants_table),
          sic.TOTAL_VARIANTS: data_extractor().read_somatic_mutation_totals(total_variants_file),
          rc.HAS_EXPRESSION_DATA: self.HAS_EXPRESSION_DATA,
          sic.VAF_PLOT: data_extractor().write_vaf_plot(work_dir)
      }
      data['results'] = results
      #TODO: add actionable stuff to merge
      mutations_annotated_path = os.path.join(work_dir, sic.MUTATIONS_EXTENDED_ONCOGENIC)
      data['merge_inputs']['treatment_options_merger'] =  data_extractor().build_therapy_info(mutations_annotated_path, oncotree_code)
      #TODO: add all gene names to merge
      return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
      required = [
            sic.MAF_FILE,
            'oncotree_code',
            'tumour_id',
            'normal_id',
            'cbio_id'
        ]
      for key in required:
          self.add_ini_required(key)
      discovered = [
            sic.CNA_FILE
        ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
      self.set_priority_defaults(self.PRIORITY)
