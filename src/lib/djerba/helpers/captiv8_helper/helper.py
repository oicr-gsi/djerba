
import os
import sys
import csv
import gzip
import logging
import time
import subprocess
from djerba.util.subprocess_runner import subprocess_runner
import djerba.core.constants as core_constants
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.util.environment import directory_finder

class main(helper_base):

  # Required parameter names for INI
  DONOR = 'donor'
  TUMOUR_ID = 'tumour_id' 
  ONCOTREE_CODE = 'oncotree_code'
  PRIMARY_CANCER = 'primary_cancer'
  IS_HEME = 'is_hemeotological_cancer' # defaults to false
  SITE_OF_BIOPSY = 'site_of_biopsy'
  RSEM_FILE = 'rsem_file'
  CIBERSORT_FILE = 'cibersort_file'
  VCF_FILE = 'vcf_file'
  VIRUS_FILE = 'virus_file'
  REPORT_DIR = 'report_dir'

  # Configure constants
  DONOR = 'donor'
  VIRUS_FILE = 'virus_file'
  VIRUS_RESULTS_SUFFIX = 'virusbreakend.vcf.summary.tsv'

  # Constants
  COLREC_ONCOTREE_CODES = ["COADREAD", "COAD", "CAIS", "MACR", "READ", "SRCCR"]
  # Driver viruses from: https://github.com/hartwigmedical/hmftools/blob/master/virus-interpreter/src/test/resources/virus_interpreter/real_virus_reporting_db.tsv
  DRIVER_VIRUSES = ["Human gammaherpesvirus 4", 
                    "Hepatitis B virus",
                    "Human gammaherpesvirus 8",
                    "Alphapapillomavirus 11",
                    "Alphapapillomavirus 5",
                    "Alphapapillomavirus 6",
                    "Alphapapillomavirus 7",
                    "Alphapapillomavirus 9",
                    "Alphapapillomavirus 1",
                    "Alphapapillomavirus 10",
                    "Alphapapillomavirus 13",
                    "Alphapapillomavirus 3",
                    "Alphapapillomavirus 8",
                    "Human polyomavirus 5"]
  SWISNF_GENES = ['SMARCB1', 'SMARCA4', 'ARID1A', 'ARID1B', 'PBRM1']
  SPECIES = 'name_species' 
  BED_FILE_NAME = '/gencode.v31.ensg_annotation_w_entrez.bed'

  # Output constants
  PATIENT = 'patient'
  ID = 'lib'
  CIBERSORT_PATH = 'cibersort'
  RSEM_PATH = 'rsem'
  TMB_VALUE = 'tmbur'
  SWI_SNF = 'swisnf'
  COLORECTAL = 'colorectal'
  LYMPH = 'lymph'
  VIRUS = 'virus'
  
  # Name for output file
  OUTPUT = '/captiv8_input.txt'
  
  # Priority
  PRIORITY = 100

  def specify_params(self):
      self.logger.debug("Specifying params for captiv8")
      discovered = [
        self.DONOR,
        self.TUMOUR_ID,
        self.ONCOTREE_CODE,
        self.SITE_OF_BIOPSY,
        self.PRIMARY_CANCER,
        self.RSEM_FILE,
        self.CIBERSORT_FILE,
        self.VCF_FILE, # for TMB
        self.VIRUS_FILE,
        self.REPORT_DIR
      ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(self.IS_HEME, False)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')


  def configure(self, config):
      """
      Needs to write the json to the workspace in the configure step
      """
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      
      # Get parameters
      wrapper = self.update_wrapper_if_null(
          wrapper,
          input_params_helper.INPUT_PARAMS_FILE,
          self.DONOR,
          input_params_helper.DONOR
      )
      wrapper = self.update_wrapper_if_null(
          wrapper,
          core_constants.DEFAULT_SAMPLE_INFO,
          self.TUMOUR_ID
      )
      wrapper = self.update_wrapper_if_null(
          wrapper,
          input_params_helper.INPUT_PARAMS_FILE,
          self.ONCOTREE_CODE,
          input_params_helper.ONCOTREE_CODE
      )
      wrapper = self.update_wrapper_if_null(
          wrapper,
          input_params_helper.INPUT_PARAMS_FILE,
          self.SITE_OF_BIOPSY,
          input_params_helper.SITE_OF_BIOPSY
      )
      wrapper = self.update_wrapper_if_null(
          wrapper,
          input_params_helper.INPUT_PARAMS_FILE,
          self.PRIMARY_CANCER,
          input_params_helper.PRIMARY_CANCER
      )


      # For now, instead of doing any provenance searching, just put the files manually in the config.
      if wrapper.my_param_is_null(self.VIRUS_FILE):
          wrapper.set_my_param(self.VIRUS_FILE, config[self.identifier][self.VIRUS_FILE])
      if wrapper.my_param_is_null(self.VCF_FILE):
          wrapper.set_my_param(self.VCF_FILE, config[self.identifier][self.VCF_FILE]) 
      if wrapper.my_param_is_null(self.RSEM_FILE):
          wrapper.set_my_param(self.RSEM_FILE, config[self.identifier][self.RSEM_FILE])
      if wrapper.my_param_is_null(self.CIBERSORT_FILE):
          wrapper.set_my_param(self.CIBERSORT_FILE, config[self.identifier][self.CIBERSORT_FILE]) 
      if wrapper.my_param_is_null(self.REPORT_DIR):
          wrapper.set_my_param(self.REPORT_DIR, config[self.identifier][self.REPORT_DIR])

      return wrapper.get_config()


  def extract(self, config):
      """
      Write the output for input into the captiv8 plugin
      """
      self.validate_full_config(config)

      # Extraction for CAPTIV-8: 
      # - Check if sample type has "lymph" in the name or if primary cancer is a hematological cancer (set lymph = yes/no)
      # - Check MAF and CNV files for the following: 
      #    is there a loss of function mutation (SNV, SV) or deep deletion of one of the following genes: 
      #    SMARCB1, SMARCA4, ARID1A, ARID1B, PBRM1. Deep deletion should be homozygous, but lof mutation e.g. stop gain can be heterozygous.
      #    (set swisnf = yes/no)
      # - Check for driver viruses (set virus = yes/no)
      # - Set tmbur = TMB thing from workflow?
      
      wrapper = self.get_config_wrapper(config)  
      
      # Get directories
      finder = directory_finder(self.log_level, self.log_path)
      work_dir = self.workspace.get_work_dir()
      data_dir = finder.get_data_dir()
      r_script_dir = finder.get_base_dir() + "/helpers/captiv8_helper/"
      bed_file = data_dir + self.BED_FILE_NAME

      #data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
       
      data = {
      'plugin_name': 'CAPTIV-8',
      #'version': self.PLUGIN_VERSION,
      'priorities': wrapper.get_my_priorities(),
      'attributes': wrapper.get_my_attributes(),
      'merge_inputs': {},
      'results': {
          self.PATIENT: config[self.identifier][self.DONOR],
          self.ID: config[self.identifier][self.TUMOUR_ID],
          self.CIBERSORT_PATH: config[self.identifier][self.CIBERSORT_FILE],
          self.RSEM_PATH: config[self.identifier][self.RSEM_FILE], 
          self.TMB_VALUE: self.get_tmb_value(config[self.identifier][self.VCF_FILE]),
          self.SWI_SNF: self.is_swisnf(config[self.identifier][self.REPORT_DIR]),
          self.COLORECTAL: self.is_colorectal(config[self.identifier][self.ONCOTREE_CODE]),
          self.LYMPH: self.is_lymph(config[self.identifier][self.SITE_OF_BIOPSY], config[self.identifier][self.IS_HEME]),
          self.VIRUS: self.is_virus(config[self.identifier][self.VIRUS_FILE])
           }
       }

      with open(work_dir + self.OUTPUT, "w") as file:
          for key, value in data['results'].items():
              file.write(str(key) + "\t" + str(value) + "\n")

      self.run_R_code(r_script_dir, data_dir, work_dir, bed_file, work_dir+self.OUTPUT)

  def run_R_code(self, r_script_dir, data_dir, work_dir, bed_file, captiv8_input):

    cmd = [
        'Rscript', r_script_dir + "/captiv8.R",
        '--meta', captiv8_input,
        '--outdir', work_dir,
        '--bed', bed_file,
    ]

    runner = subprocess_runner()
    result = runner.run(cmd, "Captiv8 R script")
    return result

  def get_tmb_value(self, vcf_file):
      tmb_script = "/.mounts/labs/CGI/scratch/aalam/tmb_for_captiv8.sh"
      tmb_value = subprocess.check_output([tmb_script, vcf_file])
      # It returns b'string\n' so convert it to a float
      tmb_value = float(tmb_value.decode('utf-8').strip())
      return tmb_value

  def is_swisnf(self, report_dir):
      
      # Check status of SWISNF genes for CAPTIV-8
      # Conservative check; any non-silent mutation is flagged as potential LOF
      
      cna_path = os.path.join(report_dir, 'data_CNA.txt')
      mut_path = os.path.join(report_dir, 'data_mutations_extended.txt')
      
      if not (os.access(cna_path, os.R_OK) and os.access(mut_path, os.R_OK)):
          print("Expected files data_CNA.txt and data_mutations_extended.txt not readable, check input directory")
          sys.exit(1)

      potential_lof = False
      
      with open(cna_path) as cna_file:
          reader = csv.reader(cna_file, delimiter="\t")
          first = True
          for row in reader:
              if first:
                  first = False
                  continue
              gene = row[0]
              status = int(row[1])
              if gene in self.SWISNF_GENES and status <= -2:
                  potential_lof = True

      with open(mut_path) as mut_file:
          reader = csv.reader(mut_file, delimiter="\t")
          first = True
          for row in reader:
              if first:
                  first = False
                  continue
              gene = row[0]
              var_class = row[8]
              if gene in self.SWISNF_GENES and var_class != 'Silent':
                  potential_lof = True
      if potential_lof:
          return "yes"
      else:
          return "no"
  
  def is_colorectal(self, oncotree_code):
      if oncotree_code.upper() in self.COLREC_ONCOTREE_CODES:
          return 'yes'
      else:
          return 'no'
  
  def is_lymph(self, primary_cancer, is_heme):
      if "lymph" in primary_cancer.lower() or is_heme:
          return 'yes'
      else:
          return 'no'

  def is_virus(self, virus_file):
      """
      Reads in VIRUSBreakend file, checks against known viruses.
      """
      viruses = []
      with open(virus_file) as data_file:
          reader = csv.reader(data_file, delimiter = "\t")
          first = True
          for row in reader:
              if first:
                  first = False
                  continue
              virus = row[4]
              viruses.append(virus)
      driver_virus_present = 0
      for virus in viruses:
          if virus in self.DRIVER_VIRUSES:
              driver_virus_present = 1
          else:
              continue
      if driver_virus_present > 0:
          return "yes"
      else:
          return "no"

