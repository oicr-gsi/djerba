"""Djerba plugin for CAPTIV-8 (research) reporting"""
import os
import re
import sys
import csv
import gzip
import logging
import json
import subprocess
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants
import djerba.plugins.captiv8.constants as constants
from djerba.plugins.base import plugin_base
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.render_mako import mako_renderer
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.util.environment import directory_finder
from djerba.util.validator import path_validator

class main(plugin_base):

    PRIORITY = 3000
    PLUGIN_VERSION = '1.0'
    TEMPLATE_NAME = 'template.html'
 
    def configure(self, config):

        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)

        # Get parameters
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            constants.DONOR,
            input_params_helper.DONOR
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_SAMPLE_INFO,
            constants.TUMOUR_ID
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            constants.ONCOTREE_CODE,
            input_params_helper.ONCOTREE_CODE
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            constants.SITE_OF_BIOPSY,
            input_params_helper.SITE_OF_BIOPSY
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            input_params_helper.INPUT_PARAMS_FILE,
            constants.PRIMARY_CANCER,
            input_params_helper.PRIMARY_CANCER
        )
        
        # Get all four requierd files from path_info.json
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            constants.VIRUS_FILE,
            constants.VIRUS_WORKFLOW
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            constants.MAF_FILE,
            constants.MAF_WORKFLOW
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            constants.RSEM_FILE,
            constants.RSEM_WORKFLOW
        )
        wrapper = self.update_wrapper_if_null(
            wrapper,
            core_constants.DEFAULT_PATH_INFO,
            constants.CIBERSORT_FILE,
            constants.CIBERSORT_WORKFLOW
        )

        # The report dir will default to the current working directory if not otherwise specified.
        # But, is allowed to be something different; just needs to point to where the following are:
        # data_mutations_extended.txt, data_CNA.txt
        if wrapper.my_param_is_null(constants.REPORT_DIR):
            wrapper.set_my_param(constants.REPORT_DIR, self.workspace.get_work_dir())

        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
      
        # Get directories
        finder = directory_finder(self.log_level, self.log_path)
        work_dir = self.workspace.get_work_dir()
        data_dir = finder.get_data_dir()
        r_script_dir = os.path.join(finder.get_base_dir(), "plugins/captiv8/Rscripts")
        bed_file = os.path.join(data_dir, constants.BED_FILE_NAME)
        
        # ------------------- Create the file that will be input into the CAPTIV-8 script ------------------- #

        captiv8_input = {
            constants.PATIENT: config[self.identifier][constants.DONOR],
            constants.ID: config[self.identifier][constants.TUMOUR_ID],
            constants.CIBERSORT_PATH: config[self.identifier][constants.CIBERSORT_FILE],
            constants.RSEM_PATH: config[self.identifier][constants.RSEM_FILE],
            constants.TMB_VALUE: self.get_tmb_value(r_script_dir, config[self.identifier][constants.REPORT_DIR], config[self.identifier][constants.MAF_FILE]),
            constants.SWI_SNF: self.is_swisnf(config[self.identifier][constants.REPORT_DIR]),
            constants.COLORECTAL: self.is_colorectal(config[self.identifier][constants.ONCOTREE_CODE]),
            constants.LYMPH: self.is_lymph(config[self.identifier][constants.SITE_OF_BIOPSY], config[self.identifier][constants.IS_HEME]),
            constants.VIRUS: self.is_virus(config[self.identifier][constants.VIRUS_FILE])
        }

        with open(os.path.join(work_dir, constants.CAPTIV8_INPUT), "w") as file:
            for key, value in captiv8_input.items():
                file.write(str(key) + "\t" + str(value) + "\n")
  
        # ------------ Run the CAPTIV-8 script to get the output path for input into the graphing ------------ #
        
        # Output path is captiv8_output.txt
        self.run_captiv8(r_script_dir, data_dir, work_dir, bed_file, os.path.join(work_dir, constants.CAPTIV8_INPUT)) 
        
        # ------------------- Graph the data  ------------------- #
        captiv8_results = os.path.join(work_dir, constants.CAPTIV8_OUTPUT)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        captiv8_base64 = self.write_captiv8_plot(r_script_dir, work_dir, captiv8_results)
        eligibility_vector = self.preprocess_captiv8(captiv8_results)
        results =  {
                'files': 
                    {'captiv8_path': captiv8_results},
                'captiv8-score': int(eligibility_vector[2]),
                'eligibility': eligibility_vector[1].lower(),
                'captiv8_base64' : captiv8_base64
            }
        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
        self.logger.debug("Specifying params for captiv8")
        discovered = [
          constants.DONOR,
          constants.TUMOUR_ID,
          constants.ONCOTREE_CODE,
          constants.SITE_OF_BIOPSY,
          constants.PRIMARY_CANCER,
          constants.RSEM_FILE,
          constants.CIBERSORT_FILE,
          constants.MAF_FILE,
          constants.VIRUS_FILE,
          constants.REPORT_DIR
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(constants.IS_HEME, False)
        self.set_ini_default(core_constants.ATTRIBUTES, 'research')
        self.set_priority_defaults(self.PRIORITY)


    def run_captiv8(self, r_script_dir, data_dir, work_dir, bed_file, captiv8_input):
  
      cmd = [
          'Rscript', r_script_dir + "/captiv8.R",
          '--meta', captiv8_input,
          '--outdir', work_dir,
          '--bed', bed_file,
      ]

      runner = subprocess_runner()
      result = runner.run(cmd, "Captiv8 R script")
      return result

    def get_tmb_value(self, r_script_dir, report_dir, maf_file):
        
        total = 0
        with gzip.open(maf_file, 'rt', encoding=core_constants.TEXT_ENCODING) as data_file:
            reader = csv.reader(data_file, delimiter="\t")
            first = True
            second = True
            for row in reader:
                if first:
                    first = False
                    continue
                if second:
                    second = False
                    continue
                pass_val = row[100]
                row_t_depth = float(row[39])
                alt_count_raw = float(row[41])
                row_t_alt_count = float(alt_count_raw) if alt_count_raw != '' else 0.0
                if row_t_depth > 0:
                    vaf = row_t_alt_count/row_t_depth 
                    if vaf >= constants.VAF_CUTOFF and pass_val == "PASS":
                        total += 1
                else:
                    continue
                
        tmb_count = round(total/constants.DIVISOR, 2)
        return tmb_count

    def is_swisnf(self, report_dir):

        # Check status of SWISNF genes for CAPTIV-8
        # Conservative check; any non-silent mutation is flagged as potential LOF

        cna_path = os.path.join(report_dir, constants.DATA_CNA)
        mut_path = os.path.join(report_dir, constants.DATA_MUTATIONS_EXTENDED)

        validator = path_validator(self.log_level, self.log_path)
        for input_path in [cna_path, mut_path]:
            validator.validate_input_file(input_path)
  
        potential_lof = False

        with open(cna_path) as cna_file:
            reader = csv.reader(cna_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    first = False
                    continue
                gene = row[0]
                status = int(row[2])
                if gene in constants.SWISNF_GENES and status <= -2:
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
                if gene in constants.SWISNF_GENES and var_class not in constants.TMB_EXCLUDED:
                    potential_lof = True
        if potential_lof:
            return "yes"
        else:
            return "no"

    def is_colorectal(self, oncotree_code):
        if oncotree_code.upper() in constants.COLREC_ONCOTREE_CODES:
            return 'yes'
        else:
            return 'no'

    def is_lymph(self, primary_cancer, is_heme):
        if "lymph" in primary_cancer.lower() or is_heme == "True":
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
            if virus in constants.DRIVER_VIRUSES:
                driver_virus_present = 1
            else:
                continue
        if driver_virus_present > 0:
            return "yes"
        else:
            return "no"

    def write_captiv8_plot(self, r_script_dir, output_dir, input_file):
        args = [
            os.path.join(r_script_dir, 'plot.R'),
            '--dir', output_dir,
            '--input', input_file
        ]
        pwgs_results = subprocess_runner().run(args)
        return(pwgs_results.stdout.split('"')[1])
    
    def preprocess_captiv8(self, captiv8_file):
        with open(captiv8_file, 'r') as captiv8_data:
            reader_file = csv.reader(captiv8_data, delimiter="\t")
            for row in reader_file:
                if row[0] == "Eligibility":
                    eligibility_vector = row
        return eligibility_vector
