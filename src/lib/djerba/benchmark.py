"""
Process the GSICAPBENCH samples for benchmarking/validation:
- Detect new GSICAPBENCH runs
- Generate config and make working directories)
- (Run djerba.py with shell script to generate reports)
- Compare with previous runs
"""

import os
import json
import logging
import djerba.util.constants as constants
import djerba.util.ini_fields as ini

from glob import glob
from string import Template
from djerba.main import main
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class benchmarker(logger):

    CONFIG_FILE_NAME = 'config.ini'
    # TODO run Mavis as a pipeline workflow; for now, use fixed Mavis results
    MAVIS_DIR = '/.mounts/labs/CGI/validation_cap/djerba_cap_bench/mavis/work'
    SAMPLES = [
        "GSICAPBENCH_1219",
        "GSICAPBENCH_1232",
        "GSICAPBENCH_1233",
        "GSICAPBENCH_1273",
        "GSICAPBENCH_1275",
        "GSICAPBENCH_1288"
    ]
    REPORT_DIR_NAME = 'report'
    TEMPLATE = 'benchmark_config.ini'
    TEST_DATA = 'test_data' # identifier for test data directory

    def __init__(self, args):
        self.log_level = self.get_log_level(args.debug, args.verbose, args.quiet)
        self.log_path = args.log_path
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.input_dir = os.path.abspath(args.input_dir)
        self.output_dir = os.path.abspath(args.output_dir)
        self.dry_run = args.dry_run
        self.validator = path_validator(self.log_level, self.log_path)
        self.data_dir = os.path.join(os.environ.get('DJERBA_BASE_DIR'), constants.DATA_DIR_NAME)
        self.test_data = os.environ.get('DJERBA_TEST_DATA')
        with open(os.path.join(self.data_dir, 'benchmark_params.json')) as in_file:
            self.sample_params = json.loads(in_file.read())

    def glob_single(self, pattern):
        """Glob recursively for the given pattern; error if no results, notify if more than one"""
        self.logger.debug("Recursive glob for files matching {0}".format(pattern))
        results = sorted(glob(pattern, recursive=True))
        if len(results)==0:
            msg = "No glob results for pattern '{0}'".format(pattern)
            self.logger.error(msg)
            raise RuntimeError(msg)
        elif len(results)>1:
            msg = "Multiple glob results for pattern '{0}': {1}".format(pattern, results)+\
                  " Using {0}".format(results[-1])
            self.logger.info(msg)
        return results.pop()

    def find_inputs(self, results_dir):
        inputs = {}
        for sample in self.SAMPLES:
            inputs[sample] = {}
            inputs[sample][ini.PATIENT] = sample
            inputs[sample][ini.DATA_DIR] = self.data_dir
            inputs[sample][self.TEST_DATA] = self.test_data
            for key in [ini.TUMOUR_ID, ini.NORMAL_ID, ini.PATIENT_ID, ini.SEX]:
                inputs[sample][key] = self.sample_params[sample][key]
            pattern = '{0}/variantEffectPredictor_2.1.6/'.format(results_dir)+\
                      '**/{0}_*mutect2.filtered.maf.gz'.format(sample)
            inputs[sample][ini.MAF_FILE] = self.glob_single(pattern)
            pattern = '{0}/{1}/*summary.zip'.format(self.MAVIS_DIR, sample)
            inputs[sample][ini.MAVIS_FILE] = self.glob_single(pattern)
            pattern = '{0}/sequenza_2.1/'.format(results_dir)+\
                      '**/{0}_*_results.zip'.format(sample)
            inputs[sample][ini.SEQUENZA_FILE] = self.glob_single(pattern)
            pattern = '{0}/rsem_2.0/'.format(results_dir)+\
                      '**/{0}_*.genes.results'.format(sample)
            inputs[sample][ini.GEP_FILE] = self.glob_single(pattern)
        return inputs

    def run_reports(self, work_dir):
        for sample in self.SAMPLES:
            self.logger.info("Generating Djerba draft report for {0}".format(sample))
            config_path = os.path.join(work_dir, sample, self.CONFIG_FILE_NAME)
            report_dir = os.path.join(work_dir, sample, self.REPORT_DIR_NAME)
            self.validator.validate_output_dir(report_dir)
            args = main_draft_args(self.log_level, self.log_path, config_path, report_dir)
            main(args).run()
            self.logger.info("Finished generating Djerba draft report for {0}".format(sample))

    def run_setup(self, results_dir, work_dir):
        """For each sample, setup working directory and generate config.ini"""
        inputs = self.find_inputs(results_dir)
        self.validator.validate_output_dir(work_dir)
        template_path = os.path.join(self.data_dir, self.TEMPLATE)
        for sample in self.SAMPLES:
            self.logger.debug("Creating working directory for sample {0}".format(sample))
            sample_dir = os.path.join(work_dir, sample)
            os.mkdir(sample_dir)
            os.mkdir(os.path.join(sample_dir, self.REPORT_DIR_NAME))
            with open(template_path) as template_file:
                template_ini = Template(template_file.read())
            config = template_ini.substitute(inputs.get(sample))
            out_path = os.path.join(sample_dir, self.CONFIG_FILE_NAME)
            with open(out_path, 'w') as out_file:
                out_file.write(config)
            self.logger.debug("Finished creating working directory {0} for sample {1}".format(sample_dir, sample))
        self.logger.info("GSICAPBENCH setup complete.")

    def run(self):
        self.logger.info("Setting up working directories for GSICAPBENCH inputs from {0}".format(self.input_dir))
        self.run_setup(self.input_dir, self.output_dir)
        if self.dry_run:
            self.logger.info("Dry-run mode; omitting report generation")
        else:
            self.logger.info("Writing GSICAPBENCH reports to {0}".format(self.output_dir))
            self.run_reports(self.output_dir)
        self.logger.info("Finished.")

class main_draft_args():
    """Alternative to argument parser output from djerba.py, for launching main draft mode"""

    def __init__(self, log_level, log_path, ini_path, out_dir):
        self.debug = False
        self.quiet = False
        self.verbose = False
        if log_level == logging.DEBUG:
            self.debug = True
        elif log_level == logging.VERBOSE:
            self.verbose = True
        self.log_path = log_path
        self.subparser_name = constants.DRAFT
        self.author = 'Test Author'
        self.failed = False
        self.html = None
        self.ini = ini_path
        self.ini_out = None
        self.dir = out_dir
        self.no_archive = True
        self.target_coverage = 80
        self.wgs_only = False
