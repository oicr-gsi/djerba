"""
Plugin for genomic landscape section.
"""
import os
import csv
from djerba.plugins.base import plugin_base, DjerbaPluginError
from mako.lookup import TemplateLookup
import djerba.core.constants as core_constants
from djerba.plugins.genomic_landscape.provenance_tools import parse_file_path
from djerba.plugins.genomic_landscape.provenance_tools import subset_provenance
from djerba.util.render_mako import mako_renderer
import djerba.util.input_params_tools as input_params_tools
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.oncokb.annotator import oncokb_annotator
from djerba.util.oncokb.tools import levels as oncokb_levels
import djerba.util.oncokb.constants as okb
import djerba.plugins.genomic_landscape.constants as constants
import djerba.plugins.genomic_landscape.msi_functions as msi
import djerba.plugins.genomic_landscape.tmb_functions as tmb
import djerba.plugins.genomic_landscape.ctdna_functions as ctdna
from djerba.util.html import html_builder as hb
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.util.environment import directory_finder

class main(plugin_base):
    
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'genomic_landscape_template.html'

    # For MSI file
    MSI_RESULTS_SUFFIX = '.filter.deduped.recalibrated.msi.booted'
    MSI_WORKFLOW = 'msisensor'
    
    # For ctDNA file
    CTDNA_RESULTS_SUFFIX = 'SNP.count.txt'
    CTDNA_WORKFLOW = 'mrdetect_filter_only'
    
    def specify_params(self):

      discovered = [
           constants.DONOR,
           constants.TUMOUR_ID,
           constants.ONCOTREE_CODE,
           constants.TCGA_CODE,
           constants.PURITY_INPUT,
           constants.MSI_FILE,
           constants.CTDNA_FILE
      ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')

      # Default parameters for priorities
      self.set_ini_default('configure_priority', 100)
      self.set_ini_default('extract_priority', 1000)
      self.set_ini_default('render_priority', 500)

      # Default parameters for clinical, supplementary
      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)
      self.set_ini_default('attributes', 'clinical')

    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)

      if wrapper.my_param_is_null(constants.ONCOTREE_CODE):
          if self.workspace.has_file(input_params_helper.INPUT_PARAMS_FILE):
              data = self.workspace.read_json(input_params_helper.INPUT_PARAMS_FILE)
              oncotree_code = data[constants.ONCOTREE_CODE]
              wrapper.set_my_param(constants.ONCOTREE_CODE, oncotree_code)
          else:
              msg = "Cannot find Oncotree code; must be manually specified or "+\
                    "given in {0}".format(input_params_helper.INPUT_PARAMS_FILE)
              self.logger.error(msg)
              raise DjerbaPluginError(msg)
      
      if wrapper.my_param_is_null(constants.TCGA_CODE):
          if self.workspace.has_file(input_params_helper.INPUT_PARAMS_FILE):
              data = self.workspace.read_json(input_params_helper.INPUT_PARAMS_FILE)
              tcga_code = data[constants.TCGA_CODE]
              wrapper.set_my_param(constants.TCGA_CODE, tcga_code)
          else:
              msg = "Cannot find TCGA code; must be manually specified or "+\
                    "given in {0}".format(input_params_helper.INPUT_PARAMS_FILE)
              self.logger.error(msg)
              raise DjerbaPluginError(msg)

      if wrapper.my_param_is_null(constants.PURITY_INPUT):
          if self.workspace.has_file(input_params_helper.INPUT_PARAMS_FILE):
              data = self.workspace.read_json(input_params_helper.INPUT_PARAMS_FILE)
              purity = data[constants.PURITY_INPUT]
              wrapper.set_my_param(constants.PURITY_INPUT, purity)
          else:
              msg = "Cannot find Purity; must be manually specified or "+\
                    "given in {0}".format(input_params_helper.INPUT_PARAMS_FILE)
              self.logger.error(msg)
              raise DjerbaPluginError(msg)

      if wrapper.my_param_is_null(constants.DONOR):
          if self.workspace.has_file(input_params_helper.INPUT_PARAMS_FILE):
              data = self.workspace.read_json(input_params_helper.INPUT_PARAMS_FILE)
              donor = data[constants.DONOR]
              wrapper.set_my_param(constants.DONOR, donor)
          else:
              msg = "Cannot find Purity; must be manually specified or "+\
                    "given in {0}".format(input_params_helper.INPUT_PARAMS_FILE)
              self.logger.error(msg)
              raise DjerbaPluginError(msg)

      if wrapper.my_param_is_null(constants.TUMOUR_ID):
          if self.workspace.has_file(core_constants.DEFAULT_SAMPLE_INFO):
              data = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
              tumour_id = data['tumour_id']
              wrapper.set_my_param(constants.TUMOUR_ID, tumour_id)
          else:
              msg = "Cannot find tumour ID; must be manually specified or "+\
                  "given in {0}".format(core_constants.DEFAULT_SAMPLE_INFO)
              self.logger.error(msg)
              raise DjerbaPluginError(msg)

      # Get files for MSI, ctDNA
      donor = config[self.identifier][constants.DONOR]
      if wrapper.my_param_is_null(constants.MSI_FILE):
          wrapper.set_my_param(constants.MSI_FILE, self.get_file(donor, self.MSI_WORKFLOW, self.MSI_RESULTS_SUFFIX))
      if wrapper.my_param_is_null(constants.CTDNA_FILE):
          wrapper.set_my_param(constants.CTDNA_FILE, self.get_file(donor, self.CTDNA_WORKFLOW, self.CTDNA_RESULTS_SUFFIX))

      return config

    def extract(self, config):
      
      wrapper = self.get_config_wrapper(config)
  
      # Get directories
      finder = directory_finder(self.log_level, self.log_path)
      work_dir = self.workspace.get_work_dir()
      data_dir = finder.get_data_dir()
      r_script_dir = finder.get_base_dir() + "/plugins/genomic_landscape/Rscripts"


      # Get parameters from config 
      tumour_id = wrapper.get_my_string(constants.TUMOUR_ID)
      oncotree_code = wrapper.get_my_string(constants.ONCOTREE_CODE)
      tcga_code = wrapper.get_my_string(constants.TCGA_CODE).lower() # tcga_code is always lowercase
      purity = wrapper.get_my_string(constants.PURITY_INPUT)

      # Make a file where all the (actionable) biomarkers will go
      biomarkers_path = self.make_biomarkers_maf(work_dir)

      # Get tmb info, genomic landscape
      results = tmb.run(self, work_dir, data_dir, r_script_dir, tcga_code, biomarkers_path, tumour_id)

      # Get ctdna file, ctdna info
      ctdna_file = wrapper.get_my_string('ctdna_file')
      results[constants.CTDNA] = ctdna.run(self, work_dir, ctdna_file)

      # Get msi file, msi data
      msi_file = wrapper.get_my_string('msi_file')
      results[constants.BIOMARKERS][constants.MSI] = msi.run(self, work_dir, r_script_dir, msi_file, biomarkers_path, tumour_id)
     
      # Get purity
      results[constants.PURITY] = float(purity)*100

      # Annotate genomic biomarkers for therapy info/merge inputs
      self.build_genomic_biomarkers(work_dir, oncotree_code, tumour_id)
      merge_inputs = self.get_merge_inputs(work_dir)
      
      data = {
          'plugin_name': 'Genomic Landscape and Biomarkers (TMB, MSI)',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': merge_inputs,
          'results': results
      }

      return data

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)

    def get_file(self, donor, workflow, results_suffix):
      """
      pull data from results file
      """
      provenance = subset_provenance(self, workflow, donor)
      try:
          results_path = parse_file_path(self, results_suffix, provenance)
      except OSError as err:
          msg = "File with extension {0} not found".format(results_suffix)
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

    def get_merge_inputs(self, work_dir):
        """
        Read therapy information for merge inputs
        This is derived from the annotated biomarkers file.
        This does not build gene information (i.e. MSI and TMB are not included in the gene glossary).
        """
        # read the tab-delimited input file
        treatments = []
        treatment_option_factory = tom_factory(self.log_level, self.log_path)
        input_name = constants.GENOMIC_BIOMARKERS_ANNOTATED
        with open(os.path.join(work_dir, input_name)) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row_input in reader:
                # record therapy for all actionable alterations (OncoKB level 4 or higher)
                therapies = oncokb_levels.parse_actionable_therapies(row_input)
                for level in therapies.keys():
                    gene = 'Biomarker'
                    treatment_entry = treatment_option_factory.get_json(
                        tier = oncokb_levels.tier(level),
                        level = level,
                        gene = gene,
                        alteration = row_input['ALTERATION'],
                        alteration_url = self.get_alt_url(row_input['ALTERATION']),
                        treatments = therapies[level]
                    )
                    treatments.append(treatment_entry)
        # assemble the output
        merge_inputs = {
            'treatment_options_merger': treatments
        }
        return merge_inputs

    def get_alt_url(self, alteration):
        core_biomarker_url = "https://www.oncokb.org/gene/Other%20Biomarkers"
        if alteration == "TMB-H" or alteration == "MSI-H":
            if alteration == "TMB-H":
                alt_url = '/'.join([core_biomarker_url,"TMB-H/"])
            if alteration == "MSI-H":
                alt_url = '/'.join([core_biomarker_url,"Microsatellite%20Instability-High/"])
        return alt_url

