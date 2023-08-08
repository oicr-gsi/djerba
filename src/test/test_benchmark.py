#! /usr/bin/env python3

from test import TestBase
import os
import unittest
from copy import deepcopy
from shutil import copytree
import djerba.util.constants as constants
from djerba.benchmark import benchmarker, report_equivalence_tester

class TestReport(TestBase):

    class mock_args_compare:
        """Use instead of argparse to store params for testing"""

        def __init__(self, report_dirs):
            self.subparser_name = constants.COMPARE
            self.report_dir = report_dirs
            self.delta = 0.1
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
            self.apply_cache = True
            self.update_cache = False
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

class TestEquivalence(TestBase):

    # simplified report structure with mock expression levels
    EXAMPLE = {
        "oncogenic_somatic_CNVs": {
            "Body": [
                {
                    "Expression Percentile": 0.4,
                    "Gene": "FGFR1",
                },
                {
                    "Expression Percentile": 1.0,
                    "Gene": "FGFR4",
                }
            ]
        },
        "small_mutations_and_indels": {
            "Body": [
                {
                    "Expression Percentile": 0.5224,
                    "Gene": "CDKN2A",
                },
                {
                    "Expression Percentile": 0.9,
                    "Gene": "KRAS",
                }
            ]
        }
    }

    def test_equivalence(self):
        tester1 = report_equivalence_tester([self.EXAMPLE, self.EXAMPLE], 0.1)
        self.assertTrue(tester1.is_equivalent())
        modified = deepcopy(self.EXAMPLE)
        cnv = "oncogenic_somatic_CNVs"
        expr = "Expression Percentile"
        modified[cnv]["Body"][0][expr] = 0.7 # was 0.4
        tester2 = report_equivalence_tester([self.EXAMPLE, modified], 0.1)
        self.assertFalse(tester2.is_equivalent())
        tester3 = report_equivalence_tester([self.EXAMPLE, modified], 0.5)
        self.assertTrue(tester3.is_equivalent())
        extra = {
            "Expression Percentile": 0.9,
            "Gene": "BRCA2"
        }
        with_extra_gene = deepcopy(modified)
        with_extra_gene[cnv]["Body"].append(extra)
        tester4 = report_equivalence_tester([self.EXAMPLE, with_extra_gene], 0.5)
        self.assertFalse(tester4.is_equivalent())
        with_extra_other = deepcopy(self.EXAMPLE)
        with_extra_other["foo"] = "bar"
        tester5 = report_equivalence_tester([self.EXAMPLE, with_extra_other], 0.5)
        self.assertFalse(tester5.is_equivalent())

if __name__ == '__main__':
    unittest.main()
