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
from djerba.plugins.tar.provenance_tools import parse_file_path
from djerba.plugins.tar.provenance_tools import subset_provenance
import gsiqcetl.column
from gsiqcetl import QCETLCache
from djerba.util.render_mako import mako_renderer
import djerba.util.input_params_tools as input_params_tools

class main(plugin_base):
    
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'msi_template.html'
    
    RESULTS_SUFFIX = '.filter.deduped.realigned.recalibrated.msi.booted'
    WORKFLOW = 'msisensor'

    def specify_params(self):

      discovered = [
           'donor',
           'oncotree_code',
           'tumour_id',
           'seg_file'
      ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')

      # Default parameters for priorities
      self.set_ini_default('configure_priority', 400)
      self.set_ini_default('extract_priority', 250)
      self.set_ini_default('render_priority', 400)

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
      if wrapper.my_param_is_null('oncotree_code'):
          wrapper.set_my_param('oncotree_code', input_data['oncotree_code'])
      if wrapper.my_param_is_null('tumour_id'):
          wrapper.set_my_param('tumour_id', input_data['tumour_id'])
      if wrapper.my_param_is_null('seg_file'):
          wrapper.set_my_param('seg_file', self.get_seg_file(config[self.identifier]['donor']))
      return config

    def extract(self, config):
      
      wrapper = self.get_config_wrapper(config)

      # Get the working directory
      work_dir = self.workspace.get_work_dir()

      # Get any input parameters
      tumour_id = config[self.identifier]['tumour_id']
      oncotree_code = config[self.identifier]['oncotree_code']

      # Get the seg file from the config
      seg_file = wrapper.get_my_string('seg_file')
      
      # Filter the seg_file only for amplifications (returns None if there are no amplifications)
      amp_path = preprocess(tumour_id, oncotree_code, work_dir).preprocess_seg(seg_file)

      cnv_data = {
          'plugin_name': 'Shallow Whole Genome Sequencing (sWGS)',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': {}
      }

      # Read purity
      with open(os.path.join(work_dir, 'purity.txt'), "r") as file:
          purity = float(file.readlines()[0])


      # Check purity
      if purity >= 0.1 and amp_path:

          # Preprocess the amplification data
          preprocess(tumour_id, oncotree_code, work_dir).run_R_code(amp_path)
          
          # Get the table rows
          rows = data_builder(work_dir).build_swgs_rows()
          
          # Put the information in the results section
          cnv_data['results'][constants.BODY] = rows
          cnv_data['results'][constants.CLINICALLY_RELEVANT_VARIANTS] = len(rows)
          cnv_data['results'][constants.PASS_TAR_PURITY] = True

          # Merge treatments (if there are any)
          cna_annotated_path = os.path.join(work_dir, self.CNA_ANNOTATED)
          cnv = data_builder(work_dir)
          cnv_data['merge_inputs']['treatment_options_merger'] =  cnv.build_therapy_info(cna_annotated_path, oncotree_code)
      
      elif purity >= 0.1 and not amp_path:
          
          # There will be no rows, so just set clinically relevant variants to 0, but still pass tar purity.
          cnv_data['results'][constants.CLINICALLY_RELEVANT_VARIANTS] = 0
          cnv_data['results'][constants.PASS_TAR_PURITY] = True
          
      else:
          cnv_data['results'][constants.PASS_TAR_PURITY] = False
      
      return cnv_data

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)

    def get_seg_file(self, root_sample_name):
      """
      pull data from results file
      """
      provenance = subset_provenance(self, self.WORKFLOW, root_sample_name)
      try:
          results_path = parse_file_path(self, self.RESULTS_SUFFIX, provenance)
      except OSError as err:
          msg = "File with extension {0} not found".format(self.RESULTS_SUFFIX)
          raise RuntimeError(msg) from err
      return results_path


    def preprocess_msi(self, msi_path, report_dir):
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



# -------------TO PREPROCESS THE MSI FILE---------------

import os
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.msi.constants as constants
from djerba.plugins.msi.extract import data_builder
from djerba.sequenza import sequenza_reader
import csv
import numpy

class main(plugin_base):


  TEMPLATE_NAME = 'msi_only_template.html'

  def configure(self, config_section):
    return config_section

  def extract(self, config_section):


    params = {
        constants.AUTHOR: "Aqsa Alam",
        constants.ASSAY_TYPE: "WGTS",
        constants.COVERAGE: 80,
        constants.FAILED: False,
        #constants.ONCOKB_CACHE: self.cache_params,
        constants.ONCOTREE_CODE: "paad",
        constants.PURITY_FAILURE: False,
        constants.PROJECT: "PASS01"
    }

    # First, preprocess the msi file
    msi_path = "../plugins/msi/test/PANX_1249_Lv_M_WG_100-PM-013_LCM5.filter.deduped.realigned.recalibrated.msi.booted"
    report_dir = "../plugins/msi/test/"
    self.preprocess_msi(msi_path, report_dir)

    # Then, preprocess the seg file
    sequenza_path = HARD_CODED_PATH
    self.preprocess_seg(sequenza_path)

    # For genomic biomarkers file
    genomic_biomarkers_path = os.path.join(report_dir, constants.GENOMIC_BIOMARKERS)

    # Random, for testing
    x = int(round(data_builder().read_fga()*100, 0))
    print(x)

    # Then, do something else...
    data = {
        'plugin_name': 'Microsatellite (MSI)',
        'clinical': True,
        'failed': False,
        'merge_inputs': {},
        'results': data_builder().build_MSI_only("100-009-008_LCM2", genomic_biomarkers_path)
        #'results': data_builder().build_all(params)
    }
    return data


  def preprocess_msi(self, msi_path, report_dir):
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
    #print("Finished pre-processing")
    return out_path


  def preprocess_seg(self, sequenza_path):
    """
    Extract the SEG file from the .zip archive output by Sequenza
    Apply preprocessing and write results to tmp_dir
    Replace entry in the first column with the tumour ID
    """
    #gamma = self.config.getint(ini.DISCOVERED, ini.SEQUENZA_GAMMA)
    gamma = 400 # HARD CODED TEMPORARY
    seg_path = sequenza_reader(sequenza_path).extract_cn_seg_file(self.tmp_dir, gamma)
    out_path = os.path.join(self.tmp_dir, 'seg.txt')
    with open(seg_path, 'rt') as seg_file, open(out_path, 'wt') as out_file:
        reader = csv.reader(seg_file, delimiter="\t")
        writer = csv.writer(out_file, delimiter="\t")
        in_header = True
        for row in reader:
            if in_header:
                in_header = False
            else:
                row[0] = self.tumour_id
            writer.writerow(row)
    return out_path
