"""
Plugin for TAR SWGS.
"""

# IMPORTS
import os
import csv
import numpy
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.genomic_landscape.msi.constants as constants
import djerba.core.constants as core_constants
from djerba.plugins.tar.provenance_tools import parse_file_path
from djerba.plugins.tar.provenance_tools import subset_provenance
import gsiqcetl.column
from djerba.util.image_to_base64 import converter
from gsiqcetl import QCETLCache
from djerba.util.render_mako import mako_renderer
import djerba.util.input_params_tools as input_params_tools
from djerba.util.subprocess_runner import subprocess_runner

class main(plugin_base):
    
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'msi_template.html'
    
    RESULTS_SUFFIX = '.filter.deduped.realigned.recalibrated.msi.booted'
    WORKFLOW = 'msisensor'

    MSS_CUTOFF = 5.0
    MSI_CUTOFF = 15.0
    MSI_FILE = 'msi.txt'

    r_script_dir = '../'

    def specify_params(self):

      discovered = [
           'donor',
           'msi_file'
      ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')

      # Default parameters for priorities
      self.set_ini_default('configure_priority', 100)
      self.set_ini_default('extract_priority', 100)
      self.set_ini_default('render_priority', 100)

      # Default parameters for clinical, supplementary
      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)
      self.set_ini_default('attributes', 'clinical')

    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      
      # Get input_data.json if it exists; else return None
      input_data = input_params_tools.get_input_params_json(self)

      if wrapper.my_param_is_null('donor'):
          wrapper.set_my_param('donor', input_data['donor'])
      if wrapper.my_param_is_null('msi_file'):
          wrapper.set_my_param('msi_file', self.get_msi_file(config[self.identifier]['donor']))
      return config

    def extract(self, config):
      
      wrapper = self.get_config_wrapper(config)

      # Get the working directory
      work_dir = self.workspace.get_work_dir()

      # Get the seg file from the config
      msi_file = wrapper.get_my_string('msi_file')
      
      # Preprocess the msi file
      msi_summary = self.preprocess_msi(work_dir, msi_file)

      msi_data = {
          'plugin_name': 'MSI',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': self.assemble_MSI(work_dir, msi_summary)
      }

      return msi_data

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)

    def get_msi_file(self, donor):
      """
      pull data from results file
      """
      provenance = subset_provenance(self, self.WORKFLOW, donor)
      try:
          results_path = parse_file_path(self, self.RESULTS_SUFFIX, provenance)
      except OSError as err:
          msg = "File with extension {0} not found".format(self.RESULTS_SUFFIX)
          raise RuntimeError(msg) from err
      return results_path
    
    def preprocess_msi(self, report_dir, msi_path):
      """
      summarize msisensor file
      """
      out_path = os.path.join(report_dir, 'msi.txt')
      msi_boots = []
      with open(msi_path, 'r') as msi_file:
          reader_file = csv.reader(msi_file, delimiter="\t")
          for row in reader_file:
              msi_boots.append(float(row[3]))
      msi_perc = numpy.percentile(numpy.array(msi_boots), [0, 25, 50, 75, 100])
      with open(out_path, 'w') as out_file:
          print("\t".join([str(item) for item in list(msi_perc)]), file=out_file)
      return out_path

    def assemble_MSI(self, work_dir, msi_file_path = None):
        msi_value = self.extract_MSI(work_dir, msi_file_path)
        msi_dict = self.call_MSI(msi_value)
        msi_plot_location = self.write_biomarker_plot(work_dir, "msi")
        msi_dict[constants.METRIC_PLOT] = converter().convert_svg(msi_plot_location, 'MSI plot')
        return(msi_dict)

    def call_MSI(self, msi_value):
      """convert MSI percentage into a Low, Inconclusive or High call"""
      msi_dict = {constants.ALT: constants.MSI,
                  constants.ALT_URL: "https://www.oncokb.org/gene/Other%20Biomarkers/MSI-H",
                  constants.METRIC_VALUE: msi_value
                  }
      if msi_value >= self.MSI_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = True
          msi_dict[constants.METRIC_ALTERATION] = "MSI-H"
          msi_dict[constants.METRIC_TEXT] = "Microsatellite Instability High (MSI-H)"
      elif msi_value < self.MSI_CUTOFF and msi_value >= self.MSS_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = False
          msi_dict[constants.METRIC_ALTERATION] = "INCONCLUSIVE"
          msi_dict[constants.METRIC_TEXT] = "Inconclusive Microsatellite Instability status"
      elif msi_value < self.MSS_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = False
          msi_dict[constants.METRIC_ALTERATION] = "MSS"
          msi_dict[constants.METRIC_TEXT] = "Microsatellite Stable (MSS)"
      else:
          msg = "MSI value extracted from file is not a number"
          self.logger.error(msg)
          raise RuntimeError(msg)
      return(msi_dict)

    def extract_MSI(self, work_dir, msi_file_path = None):
      if msi_file_path == None:
          msi_file_path = os.path.join(work_dir, self.MSI_FILE_NAME)
      with open(msi_file_path, 'r') as msi_file:
          reader_file = csv.reader(msi_file, delimiter="\t")
          for row in reader_file:
              try:
                  msi_value = float(row[2])
              except IndexError as err:
                  msg = "Incorrect number of columns in msisensor row: '{0}'".format(row)+\
                        "read from '{0}'".format(os.path.join(work_dir, self.MSI_FILE_NAME))
                  self.logger.error(msg)
                  raise RuntimeError(msg) from err
      return msi_value

    def write_biomarker_plot(self, work_dir, marker):
      out_path = os.path.join(work_dir, marker+'.svg')
      args = [
          os.path.join(self.r_script_dir, 'biomarkers_plot.R'),
          '-d', work_dir
      ]
      subprocess_runner(self.log_level, self.log_path).run(args)
      self.logger.info("Wrote biomarkers plot to {0}".format(out_path))
      return out_path
