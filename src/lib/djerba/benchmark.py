"""
Process the GSICAPBENCH samples for benchmarking/validation:
- Detect new GSICAPBENCH runs (TODO)
- Generate config and make working directories
- Run main class to generate reports
- Compare with previous runs
"""

import json
import logging
import os
import sys
import unittest
import djerba.render.constants as rc
import djerba.util.constants as constants
import djerba.util.ini_fields as ini

from copy import deepcopy
from glob import glob
from string import Template
from djerba.main import main
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class benchmarker(logger):

    CONFIG_FILE_NAME = 'config.ini'
    # TODO run Mavis as a pipeline workflow; for now, use fixed Mavis results
    MAVIS_DIR = '/.mounts/labs/CGI/validation_cap/djerba_cap_bench/mavis/work'
    # TODO set random seed in MSI workflow for consistent outputs
    MSI_DIR = '/.mounts/labs/CGI/validation_cap/djerba_cap_bench/msi/work'
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
        self.log_level = self.get_args_log_level(args)
        self.log_path = args.log_path
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.args = args
        self.validator = path_validator(self.log_level, self.log_path)
        self.data_dir = os.path.join(os.environ.get('DJERBA_BASE_DIR'), constants.DATA_DIR_NAME)
        self.test_data = os.environ.get('DJERBA_TEST_DATA') # use to find abbreviated provenance file
        with open(os.path.join(self.data_dir, 'benchmark_params.json')) as in_file:
            self.sample_params = json.loads(in_file.read())

    def glob_single(self, pattern):
        """Glob recursively for the given pattern; return a single results, or None"""
        self.logger.debug("Recursive glob for files matching {0}".format(pattern))
        results = sorted(glob(pattern, recursive=True))
        if len(results)==0:
            result = None
            self.logger.debug("No glob results for pattern '{0}'".format(pattern))
        elif len(results)==1:
            result = results[0]
            self.logger.debug("Found one glob result: {0}".format(result))
        elif len(results)>1:
            result = results[-1]
            msg = "Multiple glob results for pattern '{0}': {1}".format(pattern, results)+\
                  " Using {0}".format(result)
            self.logger.debug(msg)
        return result

    def find_inputs(self, results_dir):
        inputs = {}
        for sample in self.SAMPLES:
            sample_inputs = {}
            sample_inputs[ini.PATIENT] = sample
            sample_inputs[ini.DATA_DIR] = self.data_dir
            sample_inputs[self.TEST_DATA] = self.test_data
            for key in [ini.TUMOUR_ID, ini.NORMAL_ID, ini.PATIENT_ID, ini.SEX]:
                sample_inputs[key] = self.sample_params[sample][key]
            pattern = '{0}/**/{1}_*mutect2.filtered.maf.gz'.format(results_dir, sample)
            sample_inputs[ini.MAF_FILE] = self.glob_single(pattern)
            pattern = '{0}/**/{1}/*summary.zip'.format(self.MAVIS_DIR, sample)
            sample_inputs[ini.MAVIS_FILE] = self.glob_single(pattern)
            pattern = '{0}/**/{1}_*_results.zip'.format(results_dir, sample)
            sample_inputs[ini.SEQUENZA_FILE] = self.glob_single(pattern)
            pattern = '{0}/**/{1}_*.genes.results'.format(results_dir, sample)
            sample_inputs[ini.GEP_FILE] = self.glob_single(pattern)
            pattern = '{0}/**/{1}_*.realigned.recalibrated.msi.booted'.format(self.MSI_DIR, sample)
            sample_inputs[ini.MSI_FILE] = self.glob_single(pattern)
            if any([x==None for x in sample_inputs.values()]):
                # skip samples with missing inputs, eg. for testing
                self.logger.info("Omitting sample {0}, no inputs found".format(sample))
            else:
                inputs[sample] = sample_inputs
        if len(inputs)==0:
            # require inputs for at least one sample
            msg = "No benchmark inputs found in {0} ".format(results_dir)+\
                "for any sample in {0}".format(self.SAMPLES)
            self.logger.error(msg)
            raise RuntimeError(msg)
        return inputs

    def read_and_preprocess_report(self, report_path):
        """
        Read report from a JSON file
        Replace variable elements (images, dates) with dummy values
        """
        placeholder = 'redacted for benchmark comparison'
        with open(report_path) as report_file:
            data = json.loads(report_file.read())
        for key in [
                rc.OICR_LOGO,
                rc.CNV_PLOT,
                rc.PGA_PLOT,
                rc.TMB_PLOT,
                rc.VAF_PLOT,
                rc.REPORT_DATE
        ]:
            data[constants.REPORT][key] = placeholder
        for entry in data[constants.REPORT][rc.GENOMIC_BIOMARKERS][rc.BODY]:
            # workaround for inconsistent biomarker entry formats
            if entry[rc.ALTERATION] == rc.MSI:
                entry[rc.METRIC_PLOT] = placeholder
        return data

    def run_comparison(self, report_dirs):
        name = constants.REPORT_JSON_FILENAME
        data = []
        report_paths = []
        self.logger.info("Comparing report elements, excluding supplementary data")
        self.logger.debug("Comparing reports: {0}".format(report_dirs))
        for report_dir in report_dirs:
            self.validator.validate_input_dir(report_dir)
            report_path = self.glob_single('{0}/**/{1}'.format(report_dir, name))
            if report_path == None:
                msg = "{0} not found in {1}".format(name, report_dir)
                self.logger.error(msg)
                raise RuntimeError(msg)
            self.validator.validate_input_file(report_path)
            report_paths.append(report_path)
            doc = self.read_and_preprocess_report(report_path)
            data.append(doc.get(constants.REPORT))
        self.logger.debug("Found report paths: {0}".format(report_paths))
        if os.path.samefile(report_paths[0], report_paths[1]):
            msg = "Report paths are the same file! {0}".format(report_paths)
            self.logger.error(msg)
            raise RuntimeError(msg)
        if self.args.delta < 0 or self.args.delta > 1:
            msg = "Delta must be between 0 and 1; found {0}".format(self.args.delta)
            self.logger.error(msg)
            raise ValueError(msg)
        diff = report_equivalence_tester(data, self.args.delta, self.log_level, self.log_path)
        if diff.is_equivalent():
            self.logger.info("Reports are equivalent: {0}".format(report_paths))
        else:
            self.logger.warning("Reports are NOT equivalent: {0}".format(report_paths))
            if self.log_level > logging.INFO:
                self.logger.warning("Run with --debug or --verbose for full report diff")
        self.logger.info("Report diff: {0}".format(diff.get_diff_text()))
        return diff.is_equivalent()

    def run_reports(self, input_samples, work_dir):
        self.logger.info("Reporting for {0} samples: {1}".format(len(input_samples), input_samples))
        for sample in input_samples:
            self.logger.info("Generating Djerba draft report for {0}".format(sample))
            config_path = os.path.join(work_dir, sample, self.CONFIG_FILE_NAME)
            report_dir = os.path.join(work_dir, sample, self.REPORT_DIR_NAME)
            self.validator.validate_output_dir(report_dir)
            args = main_draft_args(self.log_level,
                                   self.log_path,
                                   config_path,
                                   report_dir,
                                   self.args.apply_cache,
                                   self.args.update_cache)
            main(args).run()
            self.logger.info("Finished generating Djerba draft report for {0}".format(sample))

    def run_setup(self, results_dir, work_dir):
        """For each sample, setup working directory and generate config.ini"""
        inputs = self.find_inputs(results_dir)
        input_samples = sorted(inputs.keys())
        self.validator.validate_output_dir(work_dir)
        template_path = os.path.join(self.data_dir, self.TEMPLATE)
        for sample in input_samples:
            self.logger.debug("Setting up working directory for sample {0}".format(sample))
            sample_dir = os.path.join(work_dir, sample)
            os.mkdir(sample_dir)
            os.mkdir(os.path.join(sample_dir, self.REPORT_DIR_NAME))
            with open(template_path) as template_file:
                template_ini = Template(template_file.read())
            config = template_ini.substitute(inputs.get(sample))
            out_path = os.path.join(sample_dir, self.CONFIG_FILE_NAME)
            with open(out_path, 'w') as out_file:
                out_file.write(config)
            self.logger.info("Created working directory {0} for sample {1}".format(sample_dir, sample))
        self.logger.info("GSICAPBENCH setup complete.")
        return input_samples

    def run(self):
        run_ok = True
        if self.args.subparser_name == constants.REPORT:
            input_dir = os.path.abspath(self.args.input_dir)
            output_dir = os.path.abspath(self.args.output_dir)
            dry_run = self.args.dry_run
            self.logger.info("Setting up working directories for GSICAPBENCH inputs from {0}".format(input_dir))
            input_samples = self.run_setup(input_dir, output_dir)
            if dry_run:
                self.logger.info("Dry-run mode; omitting report generation")
            else:
                self.logger.info("Writing GSICAPBENCH reports to {0}".format(output_dir))
                self.run_reports(input_samples, output_dir)
            self.logger.info("Finished '{0}' mode.".format(constants.REPORT))
        elif self.args.subparser_name == constants.COMPARE:
            dirs = self.args.report_dir
            if len(dirs)==2:
                self.logger.info("Comparing directories {0} and {1}".format(dirs[0], dirs[1]))
                run_ok = self.run_comparison(dirs) # false if dirs are not equivalent
                if run_ok:
                    msg = "Djerba reports are equivalent."
                    self.logger.info(msg)
                else:
                    msg = "Djerba reports are not equivalent! Script will exit with returncode 1."
                    self.logger.warning(msg)
            else:
                msg = "Incorrect number of reporting directories: Expected 2, found {0}. ".format(len(dirs))+\
                      "Directories are supplied with -r/--report-dir on the command line."
                self.logger.error(msg)
                raise RuntimeError(msg)
        else:
            msg = "Unknown subparser name {0}".format(self.args.subparser_name)
            self.logger.error(msg)
            raise RuntimeError(msg)
        return run_ok

class main_draft_args():
    """Alternative to argument parser output from djerba.py, for launching main draft mode"""

    def __init__(self, log_level, log_path, ini_path, out_dir, apply_cache, update_cache):
        if apply_cache and update_cache:
            raise RuntimeError("Cannot do both apply-cache and update-cache!")
        self.debug = False
        self.quiet = False
        self.verbose = False
        if log_level == logging.DEBUG:
            self.debug = True
        elif log_level == logging.INFO:
            self.verbose = True
        elif log_level == logging.ERROR:
            self.quiet = True
        self.log_path = log_path
        self.subparser_name = constants.DRAFT
        self.author = 'Test Author'
        self.failed = False
        self.html = None
        self.ini = ini_path
        self.ini_out = None
        self.dir = out_dir
        self.no_archive = True
        self.no_cleanup = True
        self.apply_cache = apply_cache
        self.update_cache = update_cache
        self.wgs_only = False

class report_equivalence_tester(logger):

    def __init__(self, data, expression_delta, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.data = data
        self.delta = expression_delta
        diff = ReportDiff(self.data)
        self.diff_text = diff.get_diff()
        if diff.is_identical():
            self.logger.info("EQUIVALENT: Reports are identical")
            self.equivalent = True
        elif self.expressions_are_equivalent():
            # check for non-expression discrepancies
            diff_no_expr = ReportDiff(self.remove_expression())
            self.equivalent = diff_no_expr.is_identical()
            if self.equivalent:
                msg = "EQUIVALENT: Reports are not identical, "+\
                      "but equivalent within expression tolerance"
            else:
                msg = "NOT EQUIVALENT: Expressions are within tolerance, "+\
                      "but other report fields differ"
            self.logger.info(msg)
        else:
            msg = "NOT EQUIVALENT: Expressions do not match within "+\
                  "permitted tolerance; other values may also differ"
            self.logger.info(msg)
            self.equivalent = False

    def is_equivalent(self):
        return self.equivalent

    def get_diff_text(self):
        return self.diff_text

    def expressions_are_equivalent(self):
        """
        Check if input data structures are equivalent
        Expression levels are permitted to differ by +/- delta
        """
        keys = [rc.TOP_ONCOGENIC_SOMATIC_CNVS, rc.SMALL_MUTATIONS_AND_INDELS]
        expressions = []
        # find expression by gene, for both datasets, and for both SNVs/indels and CNVs
        for doc in self.data:
            expr = {}
            for key in keys:
                for alteration in doc[key][rc.BODY]:
                    expr[alteration[rc.GENE]] = alteration[rc.EXPRESSION_METRIC]
            expressions.append(expr)
        # compare the two expression dictionaries
        if set(expressions[0].keys()) != set(expressions[1].keys()):
            self.logger.info("Expression gene sets differ, expressions are not equivalent")
            equivalent = False
        else:
            equivalent = True
            for gene in expressions[0].keys():
                expr0 = expressions[0][gene]
                expr1 = expressions[1][gene]
                if (expr0==None and expr1!=None) or (expr0!=None and expr1==None):
                    msg = "Expression levels for gene {0}".format(gene)+\
                          "have mismatched null and non-null values; "+\
                          "expressions are not equivalent"
                    self.logger.info(msg)
                    equivalent = False
                    break
                elif expr0==None and expr1==None:
                    pass # both expressions null is OK
                else:
                    diff = abs(expr0 - expr1)
                    if diff > self.delta:
                        msg = "Expression levels for gene {0} differ ".format(gene)+\
                              "by more than permitted maximum of {0}; ".format(self.delta)+\
                              "expressions are not equivalent"
                        self.logger.info(msg)
                        equivalent = False
                        break
            if equivalent:
                msg = "All expression levels are within permitted tolerance "+\
                      "of {0}; expressions are equivalent".format(self.delta)
                self.logger.info(msg)
        return equivalent

    def remove_expression(self):
        # return a copy of the Djerba report with expression values zeroed out
        data_copy = deepcopy(self.data)
        keys = [rc.TOP_ONCOGENIC_SOMATIC_CNVS, rc.SMALL_MUTATIONS_AND_INDELS]
        for doc in data_copy:
            for key in keys:
                for alteration in doc[key][rc.BODY]:
                    alteration[rc.EXPRESSION_METRIC] = 0
        return data_copy

    def compare_reports(self):
        diff = ReportDiff(self.data)
        self.diff_text = diff.get_diff()
        if diff.is_identical():
            self.logger.info("Equivalence TRUE: Reports are identical")
            equivalent = True
        elif self.expressions_are_equivalent(data):
            # check for non-expression discrepancies
            data_no_expr = self.remove_expression(data)
            diff_no_expr = ReportDiff(data_no_expr)
            equivalent = diff_no_expr.is_identical()
            if equivalent:
                msg = "Equivalence TRUE: Reports are not identical, "+\
                      "but equivalent within expression tolerance"
            else:
                msg = "Equivalence FALSE: Expressions are within tolerance, "+\
                      "but other report fields differ"
            self.logger.info(msg)
        else:
            msg = "Equivalence FALSE: Expressions differ by greater than "+\
                  "permitted tolerance; other values may also differ."
            self.logger.info(msg)
            equivalent = False
        return equivalent

class ReportDiff(unittest.TestCase):
    """Use a test assertion to diff two data structures"""

    def __init__(self, data):
        super().__init__()
        self.data = data
        if len(data)!=2:
            raise RuntimeError("Expected 2 inputs, found {0}".format(len(data)))
        self.maxDiff = None
        try:
            self.assertEqual(data[0], data[1])
            self.diff='NONE'
            self.identical = True
        except AssertionError as err:
            self.diff = str(err)
            self.identical = False

    def get_diff(self):
        return self.diff

    def is_identical(self):
        return self.identical
