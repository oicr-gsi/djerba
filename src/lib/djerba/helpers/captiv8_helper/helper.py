
import os
import sys
import csv
import gzip
import logging
import time
import subprocess
import djerba.core.constants as core_constants
import djerba.util.ini_fields as ini  # TODO new module for these constants?
import djerba.util.provenance_index as index
from djerba.helpers.base import helper_base



class main(helper_base):

  # Required parameter names for INI
  DONOR = 'donor'
  TUMOUR_ID = 'tumour_id' 
  ONCOTREE_CODE = 'oncotree_code'
  SAMPLE_TYPE = 'sample_type'
  IS_HEME = 'haemotological_cancer_type' # defaults to false
  SITE_OF_BIOPSY = 'site_of_biopsy'
  RSEM_FILE = 'rsem_file'
  CIBERSORT_FILE = 'cibersort_file'
  VCF_FILE = 'vcf_file'
  VIRUS_FILE = 'virus_file'

  # Configure constants
  DONOR = 'donor'
  VIRUS_FILE = 'virus_file'
  VIRUS_RESULTS_SUFFIX = 'virusbreakend.vcf.summary.tsv'

  # Constants
  COLREC_ONCOTREE_CODES = ["COADREAD", "COAD", "CAIS", "MACR", "READ", "SRCCR"]
  DRIVER_VIRUSES = ["Human gammaherpesvirus 4", # from https://github.com/hartwigmedical/hmftools/blob/master/virus-interpreter/src/test/resources/virus_interpreter/real_virus_reporting_db.tsv
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
  OUTPUT = '_________.txt'
  
  # Priority
  PRIORITY = 100

  def specify_params(self):
      self.logger.debug("Specifying params for captiv8")
      discovered = [
        self.DONOR,
        self.TUMOUR_ID,
        self.ONCOTREE_CODE,
        self.SAMPLE_TYPE,
        self.SITE_OF_BIOPSY,
        self.IS_HEME,
        self.RSEM_FILE,
        self.CIBERSORT_FILE,
        self.VCF_FILE, # for TMB
        self.VIRUS_FILE
      ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(
          oncokb_constants.ONCOKB_CACHE,
          oncokb_constants.DEFAULT_CACHE_PATH
      )
      self.set_ini_default(oncokb_constants.APPLY_CACHE, False)
      self.set_ini_default(oncokb_constants.UPDATE_CACHE, False)
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
          input_params_helper.PRIMARY_CANCER
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
          self.SAMPLE_TYPE,
          input_params_helper.SAMPLE_TYPE
      )
      wrapper = self.update_wrapper_if_null(
          wrapper,
          input_params_helper.INPUT_PARAMS_FILE,
          sic.PRIMARY_CANCER,
          input_params_helper.PRIMARY_CANCER
      )


      if wrapper.my_param_is_null(self.VIRUS_FILE):
          wrapper.set_my_param(self.VIRUS_FILE, config[self.identifier][self.VIRUS_FILE])
      if wrapper.my_param_is_null(self.VCF_FILE):
          wrapper.set_my_param(self.VCF_FILE, config[self.identifier][self.VCF_FILE]) # example: /.mounts/labs/prod/vidarr/output-clinical/9de4/24ae/763e/9de424ae763e9fb40dc478f779feb4659547b0a6106374e0c1e7a0eb379d429c/PANX_1615_Lv_M_WG_100-JHU-022_LCM3.mutect2.filtered.vcf.gz
      if wrapper.my_param_is_null(self.RSEM_FILE):
          wrapper.set_my_param(self.RSEM_FILE, config[self.identifier][self.RSEM_FILE])
      if wrapper.my_param_is_null(self.CIBERSORT_FILE):
          wrapper.set_my_param(self.CIBERSORT_FILE, config[self.identifier][self.CIBERSORT_FILE]) # example: /.mounts/labs/prod/vidarr/output-clinical/9de4/24ae/763e/9de424ae763e9fb40dc478f779feb4659547b0a6106374e0c1e7a0eb379d429c/PANX_1615_Lv_M_WG_100-JHU-022_LCM3.mutect2.filtered.vcf.gz
  


      return wrapper.get_config()


  def extract(self, config):
      """
      Write the output for input into the captiv8 plugin
      """
      self.validate_full_config(config)

      # Extraction for CAPTIV-8: 
      # - Set patient = donor
      # - Set lib = tumour_id
      # - Set cibersort = /path/to/cibersort/file
      # - Set rsem = /path/to/genes.results/file
      # - Check if oncotree code is a colorectal cancer type (set colorecal = yes/no)
      #   if oncotree_code.upper() in ["COADREAD", "COAD", "CAIS", "MACR", "READ", "SRCCR"]
      # - Check if sample type has "lymph" in the name or if primary cancer is a hematological cancer (set lymph = yes/no)
      # - Check MAF and CNV files for the following: 
      #    is there a loss of function mutation (SNV, SV) or deep deletion of one of the following genes: 
      #    SMARCB1, SMARCA4, ARID1A, ARID1B, PBRM1. Deep deletion should be homozygous, but lof mutation e.g. stop gain can be heterozygous.
      #    (set swisnf = yes/no)
      # - Check for driver viruses (set virus = yes/no)
      # - Set tmbur = TMB thing from workflow?
      
      wrapper = self.get_config_wrapper(config)  
      work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
      
      data = {
      'plugin_name': 'CAPTIV-8',
      'version': self.PLUGIN_VERSION,
      'priorities': wrapper.get_my_priorities(),
      'attributes': wrapper.get_my_attributes(),
      'merge_inputs': {},
      'results': {
          self.PATIENT: config[self.identifier][self.DONOR],
          self.ID = config[self.identifier][self.TUMOUR_ID],
          self.CIBERSORT_PATH = config[self.identifier][self.CIBERSORT_PATH],
          self.RSEM_PATH = config[self.identifier][self.RSEM_PATH], 
          self.TMB_VALUE = self.get_tmb_value(config[self.identifier][self.VCF_FILE],
          self.SWI_SNF = self.is_swisnf(path/to/report/dir),
          self.COLORECTAL = self.is_colorectal(config[self.identifier][self.ONCOTREE_CODE],
          self.LYMPH = self.is_lymph(config[self.identifier][self.SITE_OF_BIOPSY], config[self.identifier][self.IS_HEME]),
          self.VIRUS = self.is_virus(config[self.identifier][self.VIRUS_FILE]
           }
       }

      # Look in virus file to see if virus matches any of those in the reporting DB

      # WRITE OUTPUT FILE
  def get_tmb_value(self, vcf_file):
    tmb_script = "/path/to/tmb_for_captiv8.sh"
    tmb_value = subprocess.check_call(["./" + tmb_script, vcf_file])
    return tmb_value

  def is_virus(self, virus_file):   
    """
    Reads in VIRUSBreakend file, checks against known viruses.
    """
    viruses = []
    with open(os.path.join(work_dir, virusbreakend_path)) as data_file:
        for input_row in csv.DictReader(data_file, delimiter="\t"):
            virus = input_row[self.SPECIES]
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
                                               
  def is_colorectal(self, oncotree_code):
      if oncotree_code.upper() in self.COLREC_ONCOTREE_CODES:
          return 'yes'
      else:
          return 'no'
  
  def is_swisnf(self, report_dir):
      # Check status of SWISNF genes for CAPTIV-8
      # Conservative check; any non-silent mutation is flagged as potential LOF
      cna_path = os.path.join(report_dir, 'data_CNA.txt')
      mut_path = os.path.join(report_dir, 'data_mutations_extended.txt')
      if not (os.access(cna_path, os.R_OK) and os.access(mut_path, os.R_OK)):
          print("Expected files data_CNA.txt and data_mutations_extended.txt not readable, check input directory")
          sys.exit(1)
      ​
      genes = ['SMARCB1', 'SMARCA4', 'ARID1A', 'ARID1B', 'PBRM1']
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
              if gene in genes and status <= -2:
                  potential_lof = True

      with open(mut_path) as mut_file:
          reader = csv.reader(mut_file, delimiter="\t")
          first = True
          for	row in	reader:
              if first:
                  first = False
                  continue
          gene = row[0]
          var_class = row[8]
          if gene in genes and var_class != 'Silent':
              potential_lof = True
      ​
      if potential_lof:
          return "yes"
      else:
          return "no"
