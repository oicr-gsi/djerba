#! /usr/bin/env python3

import logging
import mako
import os
import re
import unittest
import djerba.util.ini_fields as ini

from configparser import ConfigParser
from glob import glob

from djerba.util.benchmark import benchmarker, report_equivalence_tester, \
    DjerbaReportDiffError
from djerba.util.environment import directory_finder
from djerba.util.render_mako import mako_renderer
from djerba.util.testing.tools import TestBase


class TestBenchmark(TestBase):

    class mock_report_args:
        """Use instead of argparse to store params for testing"""

        INPUT_DIR_VAR = 'DJERBA_GSICAPBENCH_INPUTS'

        def __init__(self, output_dir, dry_run):
            self.subparser_name = 'generate'
            input_dir = os.environ.get(self.INPUT_DIR_VAR)
            if input_dir==None:
                raise RuntimeError("Need to set {0} env var".format(self.INPUT_DIR_VAR))
            elif not os.path.isdir(input_dir):
                raise OSError("Input dir '{0}' is not a directory".format(input_dir))
            else:
                self.input_dir = input_dir
            if not os.path.isdir(output_dir):
                raise OSError("Output dir '{0}' is not a directory".format(output_dir))
            else:
                self.output_dir = output_dir
            self.dry_run = dry_run
            self.apply_cache = True
            self.update_cache = False
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_report_dry_run(self):
        args = self.mock_report_args(self.tmp_dir, dry_run=True)
        benchmarker(args).run()
        for sample in benchmarker.SAMPLES:
            ini_path = os.path.join(self.tmp_dir, sample, 'config.ini')
            self.assertTrue(os.path.isfile(ini_path))
            cp = ConfigParser()
            cp.read(ini_path)
            sections = cp.sections()
            self.assertEqual(len(sections), 15)
            self.assertTrue('core' in sections)

    def test_report(self):
        args = self.mock_report_args(self.tmp_dir, dry_run=False)
        bench = benchmarker(args)
        bench.run()
        private_dir = directory_finder().get_private_dir()
        report_pattern = '*report.json'
        for sample in benchmarker.SAMPLES:
            # use glob to find old/new paths for each sample
            old_pattern = os.path.join(private_dir, 'benchmarking', sample, report_pattern)
            old_path = glob(old_pattern)[0]
            new_pattern = os.path.join(self.tmp_dir, sample, 'report', report_pattern)
            new_glob = glob(new_pattern)
            self.assertEqual(len(new_glob), 1) # fails if output file was not found
            new_path = new_glob[0]
            tester = report_equivalence_tester([old_path, new_path], log_level=logging.INFO)
            self.assertTrue(tester.is_equivalent())

class TestReportEquivalence(TestBase):

    def test(self):
        test_root = directory_finder().get_test_dir()
        test_dir = os.path.join(test_root, 'util', 'compare')
        report_basic = os.path.join(test_dir, '100-009-005_LCM3-v1_report.json')
        report_copy = os.path.join(test_dir, '100-009-005_LCM3-v1_report.copy.json')
        report_broken = os.path.join(test_dir, '100-009-005_LCM3-v1_report.broken.json')
        report_other_sample = os.path.join(test_dir, '100-009-006_LCM3-v1_report.json')
        report_modified = os.path.join(test_dir, '100-009-005_LCM3-v1_report.modified.json')
        with self.assertRaises(DjerbaReportDiffError):
            inputs = [report_basic, report_basic]
            report_equivalence_tester(inputs, log_level=logging.CRITICAL)
        with self.assertRaises(DjerbaReportDiffError):
            inputs = [report_basic, '/dummy/file/path']
            report_equivalence_tester(inputs, log_level=logging.CRITICAL)
        ret1 = report_equivalence_tester([report_basic, report_copy])
        self.assertTrue(ret1.is_equivalent())
        with self.assertLogs() as cm2:
            inputs2 = [report_basic, report_broken]
            lp = os.path.join(self.tmp_dir, 'diff2.log')
            ret2 = report_equivalence_tester(inputs2, log_level=logging.INFO, log_path=lp)
            self.assertFalse(ret2.is_equivalent())
        expected2 =  "NOT EQUIVALENT: Metrics with non-zero tolerance are within "+\
            "permitted range, but other metrics differ."
        self.assertTrue(any([re.search(expected2, x) for x in cm2.output]))
        inputs3 = [report_basic, report_other_sample]
        ret3 = report_equivalence_tester(inputs3, log_level=logging.ERROR)
        self.assertFalse(ret3.is_equivalent())
        with self.assertLogs() as cm4:
            inputs4 = [report_basic, report_modified]
            lp = os.path.join(self.tmp_dir, 'diff4.log')
            ret4 = report_equivalence_tester(inputs4, log_level=logging.INFO, log_path=lp)
            self.assertTrue(ret4.is_equivalent())
        expected4 = "EQUIVALENT: Reports are not identical, but equivalent within tolerance"
        self.assertTrue(any([re.search(expected4, x) for x in cm4.output]))

class TestMakoRenderer(TestBase):

    def setUp(self):
        super().setUp() # includes tmp_dir
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))
    
    def test(self):
        mrend = mako_renderer(self.test_source_dir)
        test_template = mrend.get_template(self.test_source_dir, 'mako_template.html')
        self.assertIsInstance(test_template, mako.template.Template)
        args = {
            'greeting': 'Hello, world!'
        }
        with open(os.path.join(self.test_source_dir, 'mako_expected.html')) as in_file:
            expected_html = in_file.read()
        html_1 = mrend.render_template(test_template, args)
        self.assertEqual(html_1.strip(), expected_html.strip())
        html_2 = mrend.render_name('mako_template.html', args)
        self.assertEqual(html_2.strip(), expected_html.strip())

if __name__ == '__main__':
    unittest.main()

