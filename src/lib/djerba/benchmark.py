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
import sys # TODO remove after initial testing
import djerba.util.constants as constants
import djerba.util.ini_fields as ini

from glob import glob
from string import Template
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class benchmarker(logger):

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
    TEMPLATE = 'benchmark_config.ini'
    TEST_DATA = 'test_data' # identifier for test data directory

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)
        self.data_dir = os.path.join(os.environ.get('DJERBA_BASE_DIR'), constants.DATA_DIR_NAME)
        self.test_data = os.environ.get('DJERBA_TEST_DATA')
        # TODO read from data_dir as JSON
        with open(os.path.join(self.data_dir, 'benchmark_params.json')) as in_file:
            self.sample_params = json.loads(in_file.read())

    def glob_single(self, pattern):
        """Glob recursively for the given pattern; error if no results, notify if more than one"""
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

    def run_setup(self, results_dir, work_dir):
        """For each sample, setup working directory and generate config.ini"""
        inputs = self.find_inputs(results_dir)
        self.validator.validate_output_dir(work_dir)
        template_path = os.path.join(self.data_dir, self.TEMPLATE)
        for sample in self.SAMPLES:
            sample_dir = os.path.join(work_dir, sample)
            os.mkdir(sample_dir)
            os.mkdir(os.path.join(sample_dir, 'report'))
            with open(template_path) as template_file:
                template_ini = Template(template_file.read())
            config = template_ini.substitute(inputs.get(sample))
            out_path = os.path.join(sample_dir, 'config.ini')
            with open(out_path, 'w') as out_file:
                out_file.write(config)
            self.logger.debug("Set up working directory {0} for sample {1}".format(sample_dir, sample))
        self.logger.info("GSICAPBENCH setup complete.")

if __name__ == '__main__':
    benchmarker(log_level=logging.DEBUG).run_setup(sys.argv[1], sys.argv[2])

