#! /usr/bin/env python3

"""Test of the pwgs plugin"""

import os
import unittest
import tempfile

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.pwgs.analysis.plugin as analysis
import djerba.plugins.pwgs.sample.plugin as sample
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools

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
            self.MD5: '2ccca069bda912c101577a8ff6cd03e7'
        }
        self.run_basic_test(test_source_dir, params)

    def testPreprocessHbc(self):
        hbc_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/HBCs.csv")
        hbc_result = analysis.main.preprocess_hbc(self, hbc_expected_location)
        self.assertEqual(hbc_result['sites_checked'], 123616)
        self.assertEqual(hbc_result['hbc_n'], 24)

    def testPreprocessvaf(self):
        vaf_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/mrdetect.vaf.txt")
        vaf_results = analysis.main.preprocess_vaf(self, vaf_expected_location)
        self.assertEqual(vaf_results['reads_detected'], 18768)

    def testPreprocessResults(self):
        results_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/mrdetect.txt")
        results = pwgs_tools.preprocess_results(self, results_expected_location)
        self.assertEqual(results['TF'], 0.016 )
        self.assertEqual(results['pvalue'], 1.903e-05)
        self.assertEqual(results['outcome'], 'DETECTED')
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
            self.MD5: 'fc429d5a980fa71a94c924e39fb6130b'
        }
        self.run_basic_test(test_source_dir, params)

    def testPreprocessSNVcount(self):
        snv_count_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/snv.txt")
        snv_count = sample.main.preprocess_snv_count(self,snv_count_expected_location)
        self.assertEqual(snv_count, 21000)

class TestPwgSupplementaryPlugin(PluginTester):

    def testPwgsSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"pwgs-plugin/report_json/pwgs.supp.json")
        params = {
            self.INI: 'data/pwgs.supp.ini',
            self.JSON: json_location,
            self.MD5: '7abc0caa45be2b1fe8b4fe21bf41c91b'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
