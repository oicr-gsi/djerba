"""
Plugin for genomic landscape section.
"""
import re
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
from djerba.util.oncokb.tools import levels as oncokb_levels
import djerba.util.oncokb.constants as okb
import djerba.plugins.genomic_landscape.constants as constants
import djerba.plugins.genomic_landscape.msi_functions as msi
import djerba.plugins.genomic_landscape.tmb_functions as tmb
import djerba.plugins.genomic_landscape.ctdna_functions as ctdna
from djerba.util.html import html_builder as hb
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.util.oncokb.tools import gene_summary_reader

class main(plugin_base):
    
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'genomic_landscape_template.html'

    # For MSI file
    MSI_RESULTS_SUFFIX = '.filter.deduped.realigned.recalibrated.msi.booted'
    MSI_WORKFLOW = 'msisensor'
    # For ctDNA file
    CTDNA_RESULTS_SUFFIX = 'SNP.count.txt'
    CTDNA_WORKFLOW = 'mrdetect_filter_only'

    # Directories 
    r_script_dir = os.path.join(os.environ.get('DJERBA_BASE_DIR'), 'plugins/genomic_landscape/Rscripts/')
    data_dir = os.environ.get('DJERBA_RUN_DATA')

    def specify_params(self):

      discovered = [
           'donor',
           'msi_file',
           'ctdna_file'
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
      donor = config[self.identifier]['donor']
      if wrapper.my_param_is_null('msi_file'):
          wrapper.set_my_param('msi_file', self.get_file(donor, self.MSI_WORKFLOW, self.MSI_RESULTS_SUFFIX))
      if wrapper.my_param_is_null('ctdna_file'):
          wrapper.set_my_param('ctdna_file', self.get_file(donor, self.CTDNA_WORKFLOW, self.CTDNA_RESULTS_SUFFIX))

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
      oncotree_code = 'PAAD'
      tcga_code = 'paad'
      purity = 61

      # Make a file where all the (actionable) biomarkers will go
      biomarkers_path = self.make_biomarkers_maf(work_dir)

      # Get tmb info, genomic landscape
      results = tmb.run(self, work_dir, tcga_code, biomarkers_path, tumour_id)

      # Get ctdna file, ctdna info
      ctdna_file = wrapper.get_my_string('ctdna_file')
      results[constants.CTDNA] = ctdna.run(self, work_dir, ctdna_file)

      # Get msi file, msi data
      msi_file = wrapper.get_my_string('msi_file')
      results[constants.BIOMARKERS][constants.MSI] = msi.run(self, work_dir, msi_file, biomarkers_path, tumour_id)
     
      # Get purity
      results[constants.PURITY] = purity

      # Annotate genomic biomarkers for therapy info/merge inputs
      self.build_genomic_biomarkers(work_dir, oncotree_code, tumour_id)
      #merge_inputs = self.build_therapy_info(work_dir)
      merge_inputs = self.get_merge_inputs(work_dir)
      # !!!!!!!!!!!!!!!!!!NEED TO DO THE MERGE INPUTS THING!!!!!!!!!!!!!!!!!      
      
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

      # RENDER ALL JSONS TOGETHER

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
        Read gene and therapy information for merge inputs
        Both are derived from the annotated CNA file
        """
        # read the tab-delimited input file
        gene_info = []
        gene_info_factory = gim_factory(self.log_level, self.log_path)
        summaries = gene_summary_reader()
        treatments = []
        treatment_option_factory = tom_factory(self.log_level, self.log_path)
        input_name = constants.GENOMIC_BIOMARKERS_ANNOTATED
        with open(os.path.join(work_dir, input_name)) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row_input in reader:
                level = oncokb_levels.parse_max_reportable_level(row_input)
                [level, therapies] = oncokb_levels.parse_max_actionable_level_and_therapies(row_input)
                # record therapy for all actionable alterations (OncoKB level 4 or higher)
                if level != None:
                    gene = 'Biomarker'
                    treatment_entry = treatment_option_factory.get_json(
                        tier = oncokb_levels.tier(level),
                        level = level,
                        gene = gene,
                        alteration = row_input['ALTERATION'],
                        alteration_url = self.get_alt_url(row_input['ALTERATION']),
                        treatments = therapies
                    )
                    treatments.append(treatment_entry)
        # assemble the output
        merge_inputs = {
            'treatment_options_merger': treatments
        }
        return merge_inputs

    def get_alt_url(self, alteration):
        # genes argument may be a string, or an iterable of strings (it's just the gene)
        core_biomarker_url = "https://www.oncokb.org/gene/Other%20Biomarkers"
        if alteration == "TMB-H" or alteration == "MSI-H":
            if alteration == "TMB-H":
                alt_url = '/'.join([core_biomarker_url,"TMB-H/"])
            if alteration == "MSI-H":
                alt_url = '/'.join([core_biomarker_url,"Microsatellite%20Instability-High/"])
        return alt_url

