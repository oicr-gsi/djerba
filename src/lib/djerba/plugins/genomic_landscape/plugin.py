"""
Plugin for TAR SWGS.
"""

# IMPORTS
import os
import csv
import numpy
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.core.constants as core_constants
from djerba.plugins.tar.provenance_tools import parse_file_path
from djerba.plugins.tar.provenance_tools import subset_provenance
import gsiqcetl.column
from djerba.util.image_to_base64 import converter
from gsiqcetl import QCETLCache
from djerba.util.render_mako import mako_renderer
import djerba.util.input_params_tools as input_params_tools
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.oncokb.annotator import oncokb_annotator
import djerba.util.oncokb.constants as oncokb
import djerba.plugins.genomic_landscape.constants as constants
import djerba.plugins.genomic_landscape.msi_functions as msi
import djerba.plugins.genomic_landscape.tmb_functions as tmb

class main(plugin_base):
    
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'genomic_landscape_template.html'

    RESULTS_SUFFIX = '.filter.deduped.realigned.recalibrated.msi.booted'
    WORKFLOW = 'msisensor'
    r_script_dir = os.path.join(os.environ.get('DJERBA_BASE_DIR'), 'plugins/genomic_landscape/Rscripts/')
    data_dir = os.environ.get('DJERBA_RUN_DATA')

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

      # GET TUMOUR ID FROM SAMPLE JSON
      #if wrapper.my_param_is_null('tumour_id'):


      if wrapper.my_param_is_null('msi_file'):
          wrapper.set_my_param('msi_file', self.get_msi_file(config[self.identifier]['donor']))
      # CONFIGURE MSI
      # CONFIGURE TMB

      return config

    def extract(self, config):
      
      wrapper = self.get_config_wrapper(config)

      # Get the working directory
      work_dir = self.workspace.get_work_dir()

      # GET SNIPPET OF MSI JSON
      # GET SNIPPET OF TMB JSON
      # SLAP THEM TOGETHER

      #return data

      # Get the working directory
      work_dir = self.workspace.get_work_dir()
      #tumour_id = wrapper.get_my_string('tumour_id')
      tumour_id = "100-NH-040_LCM3_4_6"

      # Make a file where all the (actionable) biomarkers will go
      biomarkers_path = self.make_biomarkers_maf(work_dir)

      # Get tmb info, genomic landscape
      oncotree_code = 'paad'
      results = tmb.assemble_TMB_and_genomic_landscape(self, work_dir, oncotree_code)
      
      # Get msi file, msi data
      msi_file = wrapper.get_my_string('msi_file')
      msi_data = msi.run(self, work_dir, msi_file, biomarkers_path, tumour_id)

      # Put msi file in biomarkers data
      results[constants.BIOMARKERS].append(msi_data)
      
      # Annotate genomic biomarkers for therapy info/merge inputs
      self.build_genomic_biomarkers(work_dir, oncotree_code, tumour_id)

      
      data = {
          'plugin_name': 'Genomic Landscape and Biomarkers (TMB, MSI)',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': results
      }

      return data

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)

      # RENDER ALL JSONS TOGETHER

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

    def build_genomic_biomarkers(self, work_dir, oncotree_code, tumour_ID):
        """
        # Writes and annotates the biomarkers file in the report directory
        """
        self.logger.debug("Annotating Genomic Biomarkers")
        
        # Get input file (to be annotated)
        genomic_biomarkers_path = os.path.join(work_dir, constants.GENOMIC_BIOMARKERS)
        # Get output file (after annotation)
        genomic_biomarkers_annotated = os.path.join(work_dir, constants.GENOMIC_BIOMARKERS_ANNOTATED)
        # Annotate the input file to the output file 
        oncokb_annotator(
            tumour_ID,
            oncotree_code.upper(),
            work_dir,
            cache_params = None,
            log_level=self.log_level,
            log_path=self.log_path
        ).annotate_biomarkers_maf(genomic_biomarkers_path, genomic_biomarkers_annotated)
        # Return data for the biomarkers section of the output JSON
         
    def make_biomarkers_maf(self, work_dir):
        maf_header = '\t'.join(["HUGO_SYMBOL","SAMPLE_ID","ALTERATION"])
        hugo_symbol = "Other Biomarkers"
        genomic_biomarkers_path = os.path.join(work_dir, constants.GENOMIC_BIOMARKERS)
        with open(genomic_biomarkers_path, 'w') as genomic_biomarkers_file:
            # Write the header into the file 
            print(maf_header, file=genomic_biomarkers_file)
        return(genomic_biomarkers_path)

