#! /usr/bin/env python3

from test import TestBase
import os
import unittest
from shutil import copytree
import djerba.util.constants as constants
from djerba.benchmark import benchmarker

class TestBenchmark(TestBase):

    class mock_args_compare:
        """Use instead of argparse to store params for testing"""

        def __init__(self, report_dirs, compare_all=False):
            self.subparser_name = constants.COMPARE
            self.report_dir = report_dirs
            self.compare_all = compare_all
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    class mock_args_report:
        """Use instead of argparse to store params for testing"""

        def __init__(self, input_dir, output_dir):
            self.subparser_name = constants.REPORT
            self.input_dir = input_dir
            self.output_dir = output_dir
            self.dry_run = False
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_benchmark(self):
        out_dir = self.tmp_dir
        # note that the input directory only contains data for samples 1219 and 1273
        input_dir = self.bench_dir
        report_dir = os.path.join(out_dir, 'report')
        os.mkdir(report_dir)
        report_args = self.mock_args_report(input_dir, report_dir)
        self.assertTrue(benchmarker(report_args).run())
        report_1a = os.path.join(report_dir, 'GSICAPBENCH_1219')
        report_1b = os.path.join(report_dir, 'GSICAPBENCH_1219.copy')
        copytree(report_1a, report_1b) # make a copy to test identical inputs
        report_2 = os.path.join(report_dir, 'GSICAPBENCH_1273')
        compare_args_1 = self.mock_args_compare([report_1a, report_1b])
        self.assertTrue(benchmarker(compare_args_1).run())
        compare_args_2 = self.mock_args_compare([report_1a, report_2])
        self.assertFalse(benchmarker(compare_args_2).run())
        compare_args_3 = self.mock_args_compare([report_1a, report_1b], compare_all=True)
        self.assertTrue(benchmarker(compare_args_3).run())
        compare_args_4 = self.mock_args_compare([report_1a, report_2], compare_all=True)
        self.assertFalse(benchmarker(compare_args_4).run())


if __name__ == '__main__':
    unittest.main()
