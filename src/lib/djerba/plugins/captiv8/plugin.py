"""Djerba plugin for pwgs reporting"""
import os
import csv
import re
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
from djerba.plugins.captiv8.provenance_tools import parse_file_path, subset_provenance

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

        # Get files from provenance_subset.tsv.gz
        donor = config[self.identifier][constants.DONOR]
        if wrapper.my_param_is_null(constants.VIRUS_FILE):
            wrapper.set_my_param(constants.VIRUS_FILE, self.get_file(donor, constants.VIRUS_WORKFLOW, constants.VIRUS_SUFFIX))
        if wrapper.my_param_is_null(constants.VCF_FILE):
            wrapper.set_my_param(constants.VCF_FILE, self.get_file(donor, constants.VCF_WORKFLOW, constants.VCF_SUFFIX))
        if wrapper.my_param_is_null(constants.RSEM_FILE):
            wrapper.set_my_param(constants.RSEM_FILE, self.get_file(donor, constants.RSEM_WORKFLOW, constants.RSEM_SUFFIX))
        if wrapper.my_param_is_null(constants.CIBERSORT_FILE):
            wrapper.set_my_param(constants.CIBERSORT_FILE, self.get_file(donor, constants.CIBERSORT_WORKFLOW, constants.CIBERSORT_SUFFIX))
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
            constants.TMB_VALUE: self.get_tmb_value(r_script_dir, config[self.identifier][constants.VCF_FILE]),
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
          constants.VCF_FILE,
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

    def get_tmb_value(self, r_script_dir, vcf_file):
        tmb_script = os.path.join(r_script_dir, "tmb_for_captiv8.sh")
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
                if gene in constants.SWISNF_GENES and var_class != 'Silent':
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

