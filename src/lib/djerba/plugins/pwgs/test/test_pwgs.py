#! /usr/bin/env python3

"""Test of the pwgs plugin"""

import os
import unittest
import tempfile
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.pwgs.analysis.plugin as analysis
import djerba.plugins.pwgs.sample.plugin as sample

class TestPwgAnalysisPlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testPwgsAnalysis(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"pwgs-plugin/report_json/pwgs.analysis.json")
        params = {
            self.INI: 'data/pwgs.analysis.ini',
            self.JSON: json_location,
            self.MD5: '200f0f07c3e9dc2774d7ca8588fe0b1c'
        }
        self.run_basic_test(test_source_dir, params)

    def testPreprocessHbc(self):
        hbc_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/HBCs.csv")
        hbc_result = analysis.main.preprocess_hbc(self, hbc_expected_location)
        self.assertEqual(hbc_result['sites_checked'], 123616)
        self.assertEqual(hbc_result['hbc_n'], 24)

    def testPreprocessvaf(self):
        vaf_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/mrdetect.vaf.txt")
        reads_detected = analysis.main.preprocess_vaf(self,vaf_expected_location)
        self.assertEqual(reads_detected, 57)

    def testPreprocessResults(self):
        results_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/mrdetect.txt")
        results = analysis.main.preprocess_results(self,results_expected_location)
        self.assertEqual(results['TF'], 0.0321 )
        self.assertEqual(results['pvalue'], 1.903e-05)
        self.assertEqual(results['outcome'], 'POSITIVE')
        self.assertEqual(results['significance_text'], 'significantly larger')

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['pwgs_base64']:
            del data['plugins']['pwgs.analysis']['results'][key]
        return data        

class TestPwgSamplePlugin(PluginTester):

    def testPwgsSample(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"pwgs-plugin/report_json/pwgs.sample.json")
        params = {
            self.INI: 'data/pwgs.sample.ini',
            self.JSON: json_location,
            self.MD5: '3bdcf2dbc5fef05a447de844a8b75519'
        }
        self.run_basic_test(test_source_dir, params)

    def testPreprocessSNVcount(self):
        snv_count_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/snv.txt")
        snv_count = sample.main.preprocess_snv_count(self,snv_count_expected_location)
        self.assertEqual(snv_count, 21000)

if __name__ == '__main__':
    unittest.main()
