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
import djerba.core.constants as core_constants
import djerba.util.constants as constants
import djerba.util.ini_fields as ini

from configparser import ConfigParser
from copy import deepcopy
from glob import glob
from shutil import copy
from string import Template
from time import strftime

from djerba.core.loaders import plugin_loader
from djerba.core.main import main
from djerba.core.workspace import workspace
from djerba.util.environment import directory_finder
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class benchmarker(logger):

    CONFIG_FILE_NAME = 'config.ini'
    # TODO set random seed in MSI workflow for consistent outputs
    MSI_DIR_NAME = 'msi'
    DEFAULT_SAMPLES = [
        "GSICAPBENCH_1219",
        "GSICAPBENCH_1232",
        "GSICAPBENCH_1233",
        "GSICAPBENCH_1273",
        "GSICAPBENCH_1275",
        "GSICAPBENCH_1288"
    ]
    REPORT_DIR_NAME = 'report'
    TEMPLATE = 'benchmark_config.ini'

    # script modes
    GENERATE = 'generate'
    COMPARE = 'compare'

    # INI template field names
    ARRIBA_FILE = 'arriba_path'
    DONOR = 'donor'
    CTDNA_FILE = 'ctdna_file'
    HRD_FILE = 'hrd_file'
    MAF_FILE = 'maf_path'
    MAVIS_FILE = 'mavis_path'
    MRDETECT_VCF = 'mrdetect_vcf'
    MSI_FILE = 'msi_file'
    PLOIDY = 'ploidy'
    PROJECT = 'project'
    PURITY = 'purity'
    PURPLE_FILE = 'purple_path'
    RSEM_FILE = 'rsem_genes_results'
    TUMOUR_ID = 'tumour_id'
    NORMAL_ID = 'normal_id'
    APPLY_CACHE = 'apply_cache'
    UPDATE_CACHE = 'update_cache'

    def __init__(self, args):
        self.log_level = self.get_args_log_level(args)
        self.log_path = args.log_path
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.args = args
        self.plugin_loader = plugin_loader(self.log_level, self.log_path)
        self.validator = path_validator(self.log_level, self.log_path)
        dir_finder = directory_finder(self.log_level, self.log_path)
        self.data_dir = dir_finder.get_data_dir()
        self.private_dir = os.path.join(dir_finder.get_private_dir(), 'benchmarking')
        self.validator.validate_input_dir(self.private_dir)
        with open(os.path.join(self.data_dir, 'benchmark_params.json')) as in_file:
            self.sample_params = json.loads(in_file.read())
        if self.args.apply_cache and self.args.update_cache:
            msg = 'Cannot specify both --apply-cache and --update-cache'
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.samples = args.sample if args.sample else self.DEFAULT_SAMPLES 
        self.validator.validate_input_file(args.ref_path)
        self.ref_path = args.ref_path
        self.input_dir = os.path.abspath(self.args.input_dir)
        self.validator.validate_input_dir(self.input_dir)        
        self.logger.info("GSICAPBENCH input directory is '{0}'".format(self.input_dir))
        self.input_name = os.path.basename(self.input_dir)
        work_dir_root =  os.path.abspath(self.args.work_dir)
        output_dir_root = os.path.abspath(self.args.output_dir)
        self.validator.validate_output_dir(work_dir_root)
        self.validator.validate_output_dir(output_dir_root)
        # make subdirectories in work & output directories
        runtime = strftime('%Y-%m-%dT%H-%M-%S')
        dir_name = '{0}_runtime-{1}'.format(self.input_name, runtime)
        self.work_dir = os.path.join(work_dir_root, dir_name+'_work')
        self.logger.debug("Output directory is "+self.work_dir)
        os.mkdir(self.work_dir) # fails if it already exists
        self.workspace = workspace(self.work_dir, self.log_level, self.log_path)
        self.output_dir = os.path.join(output_dir_root, dir_name)
        self.logger.debug("Output directory is "+self.output_dir)
        os.mkdir(self.output_dir) # fails if it already exists

    def glob_single(self, pattern):
        """Glob recursively for the given pattern; return a single result, or None"""
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
        templates = {
            self.MAF_FILE: '{0}/**/{1}_*mutect2.filtered.maf.gz',
            self.MAVIS_FILE: '{0}/**/{1}*.mavis_summary.tab',
            self.RSEM_FILE: '{0}/**/{1}_*.genes.results',
            self.MSI_FILE: '{0}/**/{1}_*.msi.booted',
            self.CTDNA_FILE: '{0}/**/{1}_*.SNP.count.txt',
            self.ARRIBA_FILE: '{0}/**/{1}*.fusions.tsv',
            self.PURPLE_FILE: '{0}/**/{1}*.purple.zip',
            self.HRD_FILE: '{0}/**/{1}*.signatures.json'
        }
        for sample in self.samples:
            sample_inputs = {}
            sample_inputs[self.DONOR] = sample
            sample_inputs[self.PROJECT] = 'placeholder'
            sample_inputs[self.PLOIDY] = 2.0
            sample_inputs[self.APPLY_CACHE] = self.args.apply_cache
            sample_inputs[self.UPDATE_CACHE] = self.args.update_cache
            for key in [self.TUMOUR_ID, self.NORMAL_ID, self.PURITY]:
                sample_inputs[key] = self.sample_params[sample][key]
            for key in templates.keys():
                pattern = templates[key].format(results_dir, sample)
                sample_inputs[key] = self.glob_single(pattern)
            # Workaround for placeholder arriba output
            if sample_inputs[self.ARRIBA_FILE] == None:
                arriba_path = os.path.join(self.private_dir, 'arriba', 'arriba.fusions.tsv')
                if os.path.isfile(arriba_path):
                    sample_inputs[self.ARRIBA_FILE] = arriba_path
                else:
                    msg = "No arriba input found from input directory; "+\
                        "fallback arriba path '{0}' is not a file".format(arriba_path)
                    self.logger.error(msg)
                    raise RuntimeError(msg)
            if None in sample_inputs.values():
                template = "Skipping {0} as one or more values are missing: {1}"
                msg = template.format(sample, sample_inputs)
                self.logger.warning(msg)
                continue
            self.logger.debug("Sample inputs for {0}: {1}".format(sample, sample_inputs))
            if any([x==None for x in sample_inputs.values()]):
                # skip samples with missing inputs, eg. for testing
                self.logger.info("Omitting {0}, one or more inputs missing".format(sample))
            else:
                inputs[sample] = sample_inputs
        if len(inputs)==0:
            # require inputs for at least one sample
            msg = "No benchmark inputs found in {0} ".format(results_dir)+\
                "for any sample in {0}".format(self.samples)
            self.logger.error(msg)
            raise RuntimeError(msg)
        return inputs

    def run_comparison(self, reports_path, ref_path):
        config = ConfigParser()
        config.add_section('benchmark')
        config.set('benchmark', 'input_name', self.input_name)
        config.set('benchmark', 'input_file', reports_path)
        config.set('benchmark', 'ref_file', ref_path)
        self.logger.info("Loading plugin and running report comparison")
        plugin = self.plugin_loader.load('benchmark', self.workspace)
        full_config = plugin.configure(config)
        self.logger.debug("Extracting plugin data")
        data = plugin.extract(full_config)
        self.logger.debug("Rendering plugin HTML")
        html = plugin.render(data)
        return [data, html]

    def run_reports(self, input_samples, work_dir):
        self.logger.info("Reporting for {0} samples: {1}".format(len(input_samples), input_samples))
        report_paths = {}
        for sample in input_samples:
            self.logger.info("Generating Djerba draft report for {0}".format(sample))
            config_path = os.path.join(work_dir, sample, self.CONFIG_FILE_NAME)
            report_dir = os.path.join(work_dir, sample, self.REPORT_DIR_NAME)
            self.validator.validate_output_dir(report_dir)
            # run the Djerba "main" class to generate a JSON report file
            djerba_main = main(report_dir, self.log_level, self.log_path)
            config = djerba_main.configure(config_path)
            json_path = os.path.join(report_dir, sample+'_report.json')
            self.logger.debug("Extracting data to JSON path: "+json_path)
            data = djerba_main.extract(config, json_path, archive=False)
            self.logger.info("Finished Djerba draft report for {0}".format(sample))
            report_paths[sample] = json_path
        json_path = os.path.join(work_dir, 'report_paths.json')
        with open(json_path, 'w', encoding=core_constants.TEXT_ENCODING) as json_file:
            json_file.write(json.dumps(report_paths))
        return json_path

    def run_setup(self, results_dir, work_dir):
        """For each sample, set up working directory and generate config.ini"""
        self.validator.validate_input_dir(results_dir)
        inputs = self.find_inputs(results_dir)
        input_samples = sorted(inputs.keys())
        self.validator.validate_output_dir(work_dir)
        template_path = os.path.join(self.data_dir, self.TEMPLATE)
        for sample in input_samples:
            self.logger.debug("Setting up working directory for sample {0}".format(sample))
            sample_dir = os.path.join(work_dir, sample)
            if os.path.isdir(sample_dir):
                self.logger.warning("{0} exists, will overwrite".format(sample_dir))
            else:
                os.mkdir(sample_dir)
            report_dir = os.path.join(sample_dir, self.REPORT_DIR_NAME)
            if not os.path.isdir(report_dir):
                os.mkdir(report_dir)
            self.logger.debug("Reading INI template: {0}".format(template_path))
            with open(template_path) as template_file:
                template_ini = Template(template_file.read())
            self.logger.debug("Substituting with: {0}".format(inputs.get(sample)))
            config = template_ini.substitute(inputs.get(sample))
            out_path = os.path.join(sample_dir, self.CONFIG_FILE_NAME)
            with open(out_path, 'w') as out_file:
                out_file.write(config)
            self.logger.info("Created working directory {0}".format(sample_dir))
        self.logger.info("GSICAPBENCH setup complete.")
        return input_samples

    def run(self):
        # generate Djerba reports
        # load and run plugin to compare reports and generate summary
        # copy JSON/text files and write HTML summary to output directory
        input_samples = self.run_setup(self.input_dir, self.work_dir)
        reports_path = self.run_reports(input_samples, self.work_dir)
        data, html = self.run_comparison(reports_path, self.ref_path)
        self.logger.info("Writing data and HTML output")
        self.write_outputs(data, html)

    def write_outputs(self, data, html):
        # write the HTML output
        html_path = os.path.join(self.output_dir, self.input_name+'_summary.html')
        with open(html_path, 'w', encoding=core_constants.TEXT_ENCODING) as html_file:
            html_file.write(html)
        # copy JSON files, and write the diff text (if any)
        for result in data['results']['donor_results']:
            for json_path in [result['input_file'], result['ref_file']]:
                if os.path.exists(json_path):
                    copy(json_path, self.output_dir)
            # TODO put diff link filename in JSON
            # TODO only write diff if non-empty
            diff_path = os.path.join(self.output_dir, result['donor']+'_diff.txt')
            with open(diff_path, 'w', encoding=core_constants.TEXT_ENCODING) as diff_file:
                diff_file.write(result['diff'])
        self.logger.info('Finished writing summary to '+self.output_dir)

class report_equivalence_tester(logger):

    """
    Equivalence test is specific to the set of plugins in GSICAPBENCH
    Eg. expression comparison will not necessarily work with different plugins
    """

    CNV_NAME = 'wgts.cnv_purple'
    FUSION_NAME = 'fusion'
    SNV_INDEL_NAME = 'wgts.snv_indel'
    SUPPLEMENT_NAME = 'supplement.body'
    # deal with inconsistent capitalization
    BODY_KEY = {
        CNV_NAME: 'body',
        SNV_INDEL_NAME: 'Body'
    }
    XPCT_KEY = {
        CNV_NAME: 'Expression Percentile',
        SNV_INDEL_NAME: 'Expression percentile'
    }
    GENE = 'Gene'
    RESULTS = 'results'
    EXPRESSION = 'expression'
    MSI = 'msi'
    DELTA_DEFAULTS = {
        EXPRESSION: 0.1, # expression is recorded as a number, this delta is 10%
        MSI: 1.0  # MSI is recorded as a percentage, this delta is 1.0%
    }
    PLACEHOLDER = 0

    IDENTICAL_STATUS = 'identical'
    EQUIVALENT_STATUS = 'equivalent but not identical'
    NOT_EQUIVALENT_STATUS = 'not equivalent'

    def __init__(self, report_paths, delta_path=None,
                 log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        msg = None
        if len(report_paths) != 2:
            msg = "Must have exactly 2 report paths, got: {0}".format(report_paths)
        elif not os.path.isfile(report_paths[0]):
            msg = "Report path {0} is not a file".format(report_paths[0])
        elif not os.path.isfile(report_paths[1]):
            msg = "Report path {0} is not a file".format(report_paths[1])
        elif os.path.samefile(report_paths[0], report_paths[1]):
            msg = "Report paths are the same file! {0}".format(report_paths)
        if msg:
            self.logger.error(msg)
            raise DjerbaReportDiffError(msg)
        self.data = [self.read_and_preprocess_report(x) for x in report_paths]
        if delta_path:
            with open(delta_path) as delta_file:
                deltas = json.loads(delta_file.read())
            if set(deltas.keys()) != set(self.DELTA_DEFAULTS.keys()):
                msg = "Bad key set for delta config file '{0}'".format(delta_path)
                self.logger.error(msg)
                raise DjerbaReportDiffError(msg)
            self.deltas = deltas
        else:
            self.deltas = self.DELTA_DEFAULTS
        self.logger.info("Delta values by metric type: {0}".format(self.deltas))
        diff = ReportDiff(self.data)
        self.diff_text = diff.get_diff()
        self.identical = False
        if diff.is_identical():
            self.logger.info("EQUIVALENT: Reports are identical")
            self.identical = True
            self.equivalent = True
        elif self.deltas_are_equivalent():
            # check if metrics without a delta match exactly
            if self.non_deltas_are_equivalent():
                msg = "EQUIVALENT: Reports are not identical, "+\
                    "but equivalent within tolerance"
                self.logger.info(msg)
                self.equivalent = True
            else:
                msg = "NOT EQUIVALENT: Metrics with non-zero tolerance are within "+\
                    "permitted range, but other metrics differ."
                self.logger.info(msg)
                self.equivalent = False
        else:
            msg = "NOT EQUIVALENT: Reports do not match within tolerance"
            self.logger.info(msg)
            self.equivalent = False

    def deltas_are_equivalent(self):
        eq = self.expressions_are_equivalent() and \
            self.msi_values_are_equivalent()
        return eq

    def expressions_are_equivalent(self):
        """
        Check if input data structures are equivalent
        Expression levels are permitted to differ by +/- delta
        """
        equivalent = True
        for name in [self.CNV_NAME, self.SNV_INDEL_NAME]:
            plugin_eq = True
            self.logger.debug("Checking expression levels for plugin: {0}".format(name))
            expr0 = self.get_expressions_by_gene(self.data[0], name)
            expr1 = self.get_expressions_by_gene(self.data[1], name)
            delta = self.deltas[self.EXPRESSION]
            if set(expr0.keys()) != set(expr1.keys()):
                self.logger.warning("Gene sets differ, expressions are not equivalent")
                plugin_eq = False
            else:
                for gene in expr0.keys():
                    if expr0[gene] == None or expr1[gene] == None:
                        if expr0[gene] == None and expr1[gene] == None:
                            pass
                        else:
                            msg = "{0} not equivalent: Mixed null and non-null expression"
                            self.logger.debug(msg.format(gene))
                            plugin_eq = False
                    else:
                        diff = abs(expr0[gene] - expr1[gene])
                        if diff > delta:
                            template = "{0} not equivalent: Expression delta > {1} "
                            msg = template.format(gene, delta)
                            self.logger.debug(msg)
                            plugin_eq = False
            if plugin_eq:
                msg = "Expression levels for plugin {0} are equivalent".format(name)
            else:
                msg = "Expression levels for plugin {0} are NOT equivalent".format(name)
                equivalent = False
            self.logger.info(msg)
        return equivalent

    def is_equivalent(self):
        return self.equivalent

    def is_identical(self):
        return self.identical
    
    def get_diff_text(self):
        return self.diff_text

    def get_status(self):
        if self.is_identical():
            return self.IDENTICAL_STATUS
        elif self.is_equivalent():
            return self.EQUIVALENT_STATUS
        else:
            return self.NOT_EQUIVALENT_STATUS

    def get_status_emoji(self):
        status = self.get_status()
        if status == self.IDENTICAL_STATUS:
            return '&#x2705;' # white check mark
        elif status == self.EQUIVALENT_STATUS:
            return '&#x26A0;' # warning sign
        else:
            return '&#x274C;' # X mark

    def get_expressions_by_gene(self, data, plugin):
        body_key = self.BODY_KEY[plugin]
        xpct_key = self.XPCT_KEY[plugin]
        try:
            body = data[plugin][self.RESULTS][body_key]
        except KeyError:
            self.logger.error("{0}: {1}".format(plugin, data.keys()))
            raise
        expr = {}
        for item in body:
            key = item[self.GENE]
            value = item[xpct_key]
            expr[key] = value
        return expr

    def get_msi(self, report_data):
        return report_data['genomic_landscape']['results']\
            ['genomic_biomarkers']['MSI']['Genomic biomarker value']

    def msi_values_are_equivalent(self):
        msi0 = self.get_msi(self.data[0])
        msi1 = self.get_msi(self.data[1])
        delta = self.deltas[self.MSI]
        if abs(msi0 - msi1) < delta:
            self.logger.info("MSI values are equivalent")
            eq = True
        else:
            self.logger.info("MSI values are NOT equivalent")
            eq = False
        return eq

    def non_deltas_are_equivalent(self):
        # remove metrics with a non-zero tolerance range; compare the other metrics
        redacted = []
        for data_set in self.data:
            redacted_set = deepcopy(data_set)
            redacted_set = self.set_msi(redacted_set, self.PLACEHOLDER)
            for name in [self.CNV_NAME, self.SNV_INDEL_NAME]:
                redacted_set = self.set_expression(redacted_set, name, self.PLACEHOLDER)
            redacted.append(redacted_set)
        diff = ReportDiff(redacted)
        return diff.is_identical()

    def read_and_preprocess_report(self, report_path):
        """
        Read report from a JSON file
        Replace variable elements (images, dates) with dummy values
        """
        placeholder = 'redacted for benchmark comparison'
        self.logger.info("Preprocessing report path {0}".format(report_path))
        with open(report_path) as report_file:
            data = json.loads(report_file.read())
        plugins = data['plugins'] # don't compare config or core elements
        # redact plugin versions, plots, dates
        for plugin_name in plugins.keys():
            plugins[plugin_name]['version'] = placeholder
        results = 'results'
        plugins[self.CNV_NAME][results]['cnv plot'] = placeholder
        plugins[self.SNV_INDEL_NAME][results]['vaf_plot'] = placeholder
        for biomarker in ['MSI', 'TMB', 'HRD']:
            plugins['genomic_landscape'][results]['genomic_biomarkers'][biomarker]['Genomic biomarker plot'] = placeholder
        for date_key in ['extract_date', 'report_signoff_date']:
            plugins[self.SUPPLEMENT_NAME][results][date_key] = placeholder
        # redact gene descriptions; text encoding issues can cause irrelevant discrepancies
        for name in [self.CNV_NAME, self.SNV_INDEL_NAME, self.FUSION_NAME]:
            for item in plugins[name]['merge_inputs']['gene_information_merger']:
                item['Summary'] = placeholder
        return plugins

    def set_expression(self, data, plugin, value):
        # set all expressions for the given plugin to the same value
        # use to redact data and compare without expressions
        body_key = self.BODY_KEY[plugin]
        xpct_key = self.XPCT_KEY[plugin]
        try:
            body = data[plugin][self.RESULTS][body_key]
        except KeyError:
            self.logger.error("{0}: {1}".format(plugin, data.keys()))
            raise
        for item in body:
            item[xpct_key] = value
        return data

    def set_msi(self, report_data, value):
        report_data['genomic_landscape']['results']\
            ['genomic_biomarkers']['MSI']['Genomic biomarker value'] = value
        return report_data


class ReportDiff(unittest.TestCase):
    """Use a test assertion to diff two data structures"""

    def __init__(self, data):
        super().__init__()
        if len(data)!=2:
            raise DjerbaReportDiffError("Expected 2 inputs, found {0}".format(len(data)))
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

class DjerbaReportDiffError(Exception):
    pass
