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

    def specify_params(self):

      # Required parameters for swgs
      self.set_ini_default('seg_file', None)
      
      # Default parameters for priorities
      self.set_ini_default('configure_priority', 100)
      self.set_ini_default('extract_priority', 100)
      self.set_ini_default('render_priority', 100)
      #self.set_priority_defaults(self.PRIORITY)

      # Default parameters for clinical, supplementary
      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)
      self.set_ini_default('attributes', 'clinical')

    def configure(self, config):
      config = self.apply_defaults(config)
      
      # POPULATE THE INI HERE!?
      config[self.identifier]["seg_file"] = self.get_seg_file(config["provenance_helper"]["root_sample_name"])

      return config

    def extract(self, config):
      

      wrapper = self.get_config_wrapper(config)
      
      # Get the seg file from the config
      seg_file = wrapper.get_my_string('seg_file')
    

      # Pre-process all the files
      work_dir = self.workspace.get_work_dir()
      preprocess(config, work_dir, seg_file).run_R_code()

      # ADD IF STATEMENT FOR PURITY
      data = {
          'plugin_name': 'Shallow Whole Genome Sequencing (sWGS)',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': data_builder(work_dir, seg_file).build_swgs()
      }
      return data

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
