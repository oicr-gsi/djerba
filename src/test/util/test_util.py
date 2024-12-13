#! /usr/bin/env python3

import json
import logging
import mako
import os
import re
import tempfile
import unittest

from configparser import ConfigParser
from glob import glob

from djerba.util.benchmark import benchmarker, report_equivalence_tester, \
    DjerbaReportDiffError
from djerba.util.environment import directory_finder
from djerba.util.render_mako import mako_renderer
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.testing.tools import TestBase


class TestBenchmark(TestBase):

    class mock_report_args:
        """Use instead of argparse to store params for testing"""

        def __init__(self, input_dir, output_dir, ref_path, samples, work_dir=None):
            if not os.path.isdir(input_dir):
                raise OSError("Input dir '{0}' is not a directory".format(input_dir))
            else:
                self.input_dir = input_dir
            if not os.path.isdir(output_dir):
                raise OSError("Output dir '{0}' is not a directory".format(output_dir))
            else:
                self.output_dir = output_dir
            if work_dir==None:
                self.work_dir = output_dir
            elif not os.path.isdir(work_dir):
                raise OSError("Work dir '{0}' is not a directory".format(work_dir))
            else:
                self.work_dir = work_dir
            if not os.path.isfile(ref_path):
                raise OSError("Reference path '{0}' is not a file".format(ref_path))
            else:
                self.ref_path = ref_path
            self.sample = samples
            self.apply_cache = True
            self.update_cache = False
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def setUp(self):
        super().setUp() # includes tmp_dir
        private_dir = directory_finder().get_private_dir()
        self.input_dir = os.path.join(
            private_dir, 'benchmarking', 'djerba_bench_test_inputs'
        )
        self.ref_path = os.path.join(
            private_dir, 'benchmarking', 'djerba_bench_reference', 'bench_ref_paths.json'
        )
        self.samples = ['GSICAPBENCH_1219', 'GSICAPBENCH_1273', 'GSICAPBENCH_1275']

    def test_inputs(self):
        args = self.mock_report_args(self.input_dir, self.tmp_dir, self.ref_path, self.samples)
        bench = benchmarker(args)
        bench_inputs = bench.find_inputs(self.input_dir)
        self.assertEqual(sorted(list(bench_inputs.keys())), args.sample)
        for k in bench_inputs.keys():
            self.assertEqual(len(bench_inputs[k]), 16)

    def test_setup(self):
        args = self.mock_report_args(self.input_dir, self.tmp_dir, self.ref_path, self.samples)
        bench = benchmarker(args)
        samples = bench.run_setup(args.input_dir, args.work_dir)
        self.assertEqual(sorted(samples), args.sample)
        for sample in samples:
            ini_path = os.path.join(self.tmp_dir, sample, 'config.ini')
            self.assertTrue(os.path.isfile(ini_path))

    def test_outputs(self):
        out_dir = os.path.join(self.tmp_dir, 'output')
        work_dir = os.path.join(self.tmp_dir, 'work')
        os.mkdir(out_dir)
        os.mkdir(work_dir)
        args = self.mock_report_args(
            self.input_dir, out_dir, self.ref_path, self.samples, work_dir
        )
        #args.verbose = True # uncomment to view progress of report generation
        bench = benchmarker(args)
        samples = bench.run_setup(args.input_dir, args.work_dir)
        reports_path = bench.run_reports(samples, args.work_dir)
        [data, html] = bench.run_comparison(reports_path, self.ref_path)
        # check the JSON output
        self.assertEqual(len(data['results']['donor_results']), 7)
        # check the HTML output
        exclude = ['Run time:', 'Djerba core version:']
        html_lines = []
        for line in re.split("\n", html):
            if not any([re.search(x, line) for x in exclude]):
                html_lines.append(line)
        html_md5 = self.getMD5_of_string("\n".join(html_lines))
        # TODO update the md5 and output files; assertions commented out for now
        # self.assertEqual(html_md5, 'a5cd7ccd3c717975b12f8d2b2d06ff56')
        # check output files
        bench.write_outputs(data, html)
        run_dir_name = os.listdir(out_dir)[0]
        self.assertTrue(re.match('djerba_bench_test_inputs_runtime-', run_dir_name))
        output_files = sorted(os.listdir(os.path.join(out_dir, run_dir_name)))
        expected_files = [
            '100-009-005_LCM3-v1_report.json',
            '100-009-006_LCM3-v1_report.json',
            '100-009-008_LCM2-v1_report.json',
            '100-PM-018_LCM4-v1_report.json',
            '100-PM-019_LCM3-v1_report.json',
            '100_JHU_004_LCM3_6-v1_report.json',
            'GSICAPBENCH_1219_diff.txt',
            'GSICAPBENCH_1219_report.json',
            'GSICAPBENCH_1232_diff.txt',
            'GSICAPBENCH_1233_diff.txt',
            'GSICAPBENCH_1273_diff.txt',
            'GSICAPBENCH_1273_report.json',
            'GSICAPBENCH_1275_diff.txt',
            'GSICAPBENCH_1275_report.json',
            'GSICAPBENCH_1288_diff.txt',
            'djerba_bench_test_inputs_summary.html'
        ]
        # TODO update list and uncomment this assertion
        #self.assertEqual(output_files, expected_files)

class TestDiffScript(TestBase):

    def get_diff_cmd(self, report1, report2):
        cmd = [
            'diff_reports.py',
            '--verbose',
            '--report', report1,
            '--report', report2
        ]
        return cmd

    def test(self):
        test_root = directory_finder().get_test_dir()
        test_dir = os.path.join(test_root, 'util', 'compare')
        report_basic = os.path.join(test_dir, '100-009-005_LCM3-v1_report.json')
        report_copy = os.path.join(test_dir, '100-009-005_LCM3-v1_report.copy.json')
        report_broken = os.path.join(test_dir, '100-009-005_LCM3-v1_report.broken.json')
        report_other_sample = os.path.join(test_dir, '100-009-008_LCM2-v1_report.json')
        report_modified = os.path.join(test_dir, '100-009-005_LCM3-v1_report.modified.json')
        # suppress error logs; subprocess_runner needs a valid logfile, not /dev/null
        tmp = tempfile.mkdtemp(prefix='djerba_diff_test_')
        runner = subprocess_runner(log_path=os.path.join(tmp, 'diff.log'))
        result = runner.run(self.get_diff_cmd(report_basic, report_copy))
        self.assertEqual(result.returncode, 0)
        result = runner.run(self.get_diff_cmd(report_basic, report_modified))
        self.assertEqual(result.returncode, 0) # equivalent within tolerance
        cmd = self.get_diff_cmd(report_basic, report_other_sample)
        result = runner.run(cmd, raise_err=False)
        self.assertEqual(result.returncode, 1)
        cmd = self.get_diff_cmd(report_basic, report_broken)
        result = runner.run(cmd, raise_err=False)
        self.assertEqual(result.returncode, 1)


class TestReportEquivalence(TestBase):

    def test(self):
        test_root = directory_finder().get_test_dir()
        test_dir = os.path.join(test_root, 'util', 'compare')
        report_basic = os.path.join(test_dir, '100-009-005_LCM3-v1_report.json')
        report_copy = os.path.join(test_dir, '100-009-005_LCM3-v1_report.copy.json')
        report_broken = os.path.join(test_dir, '100-009-005_LCM3-v1_report.broken.json')
        report_other_sample = os.path.join(test_dir, '100-009-008_LCM2-v1_report.json')
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

