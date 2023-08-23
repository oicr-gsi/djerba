"""
Plugin for TAR SWGS.
"""

# IMPORTS
import os
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.tar.swgs.constants as constants
from djerba.plugins.tar.swgs.preprocess import preprocess
from djerba.plugins.tar.swgs.extract import data_builder 
import djerba.core.constants as core_constants
import djerba.plugins.tar.provenance_tools as provenance_tools
import gsiqcetl.column
from gsiqcetl import QCETLCache



class main(plugin_base):
    
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'swgs_template.html'
    RESULTS_SUFFIX = '.seg.txt'
    WORKFLOW = 'ichorcna'
    CNA_ANNOTATED = "data_CNA_oncoKBgenes_nonDiploid_annotated.txt"

    def specify_params(self):

      # Required parameters for swgs
      self.add_ini_discovered('seg_file')
      self.add_ini_required('root_sample_name')
      self.add_ini_required('oncotree_code')
      self.add_ini_required('tumour_id')

      # Default parameters for priorities
      self.set_ini_default('configure_priority', 400)
      self.set_ini_default('extract_priority', 250)
      self.set_ini_default('render_priority', 400)
      #self.set_priority_defaults(self.PRIORITY)

      # Default parameters for clinical, supplementary
      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)
      self.set_ini_default('attributes', 'clinical')

    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      if wrapper.my_param_is_null('seg_file'):
        config[self.identifier]["seg_file"] = self.get_seg_file(config[self.identifier]['root_sample_name'])
      return config

    def extract(self, config):
      
      wrapper = self.get_config_wrapper(config)

      # Get the working directory
      work_dir = self.workspace.get_work_dir()
  
      # Get the seg file from the config
      seg_file = wrapper.get_my_string('seg_file')
      
      # Filter the seg_file only for amplifications (returns None if there are no amplifications)
      amp_path = preprocess(config, work_dir).preprocess_seg(seg_file)

      cnv_data = {
          'plugin_name': 'Shallow Whole Genome Sequencing (sWGS)',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': {
              constants.CNV_PLOT: data_builder(work_dir).build_graph(seg_file) # graph is made from the original seg file, NOT the amplification-only seg file
          }
      }

      # Read purity
      with open(os.path.join(work_dir, 'purity.txt'), "r") as file:
          purity = float(file.readlines()[0])


      # Check purity
      if purity >= 0.1 and amp_path:

          # Preprocess the amplification data
          preprocess(config, work_dir).run_R_code(amp_path)
          
          # Get the table rows
          rows = data_builder(work_dir).build_swgs_rows()
          
          # Put the information in the results section
          cnv_data['results'][constants.BODY] = rows
          cnv_data['results'][constants.CLINICALLY_RELEVANT_VARIANTS] = len(rows)
          cnv_data['results'][constants.PASS_TAR_PURITY] = True

          # Merge treatments (if there are any)
          cna_annotated_path = os.path.join(work_dir, self.CNA_ANNOTATED)
          cnv = data_builder(work_dir)
          cnv_data['merge_inputs']['treatment_options_merger'] =  cnv.build_therapy_info(cna_annotated_path, config['tar.swgs']['oncotree_code'])
      
      elif purity >= 0.1 and not amp_path:
          
          # There will be no rows, so just set clinically relevant variants to 0, but still pass tar purity.
          cnv_data['results'][constants.CLINICALLY_RELEVANT_VARIANTS] = 0
          cnv_data['results'][constants.PASS_TAR_PURITY] = True
          
      else:
          cnv_data['results'][constants.PASS_TAR_PURITY] = False
      
      return cnv_data

    def render(self, data):
      #renderer = mako_renderer(self.get_module_dir())
      #return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

      super().render(data)
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


    def get_group_id(self, donor):
      qcetl_cache = "/scratch2/groups/gsi/production/qcetl_v1"
      etl_cache = QCETLCache(qcetl_cache)
      df = etl_cache.bamqc4merged.bamqc4merged
      df = df.set_index("Donor")
      if donor in df.index.values.tolist():
          df = df.loc[donor]
          group_id = df[df['Group ID'].str.contains("Pl")]['Group ID'][0]
          return(group_id)

    def get_seg_file(self, root_sample_name):
      """
      pull data from results file
      """
      provenance = provenance_tools.subset_provenance(self, self.WORKFLOW, root_sample_name)
      try:
          results_path = provenance_tools.parse_file_path(self, self.RESULTS_SUFFIX, provenance)
      except OSError as err:
          msg = "File with extension {0} not found".format(self.RESULTS_SUFFIX)
          raise RuntimeError(msg) from err
      return results_path
