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
from djerba.core.workspace import workspace
import djerba.plugins.pwgs.constants as constants

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
            self.MD5: '2c45c4e916784d68aa977b4351b53623'
        }
        self.run_basic_test(test_source_dir, params)

    def testPreprocessHbc(self):
        hbc_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/HBCs.csv")
        hbc_result = analysis.main.preprocess_hbc(self, hbc_expected_location)
        self.assertEqual(hbc_result[constants.SITES_CHECKED], 123616)
        self.assertEqual(hbc_result[constants.COHORT_N], 24)

    def testPreprocessvaf(self):
        vaf_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/mrdetect.vaf.txt")
        reads_detected = analysis.main.preprocess_vaf(self, vaf_expected_location)
        self.assertEqual(reads_detected, 18768)

    def testPreprocessResults(self):
        results_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/mrdetect.txt")
        results = pwgs_tools.preprocess_results(self, results_expected_location)
        self.assertEqual(results[constants.TUMOUR_FRACTION_ZVIRAN], 0.016 )
        self.assertEqual(results[constants.PVALUE], 1.903e-05)
        self.assertEqual(results[constants.CTDNA_OUTCOME], 'DETECTED')
        self.assertEqual(results[constants.SIGNIFICANCE], 'significantly larger')

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['pwgs_base64']:
            del data['plugins']['pwgs.analysis']['results'][key]
        return data        

class TestPwgSamplePlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testPwgsSample(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"pwgs-plugin/report_json/pwgs.sample.json")
        params = {
            self.INI: 'data/pwgs.sample.ini',
            self.JSON: json_location,
            self.MD5: '9743fb4c0d0eb0269d3aeb8fe6d2bee1'
        }
        self.run_basic_test(test_source_dir, params)

    def testPreprocessSNVcount(self):
        snv_count_expected_location = os.path.join(self.sup_dir ,"pwgs-plugin/snv.txt")
        snv_count = sample.main.preprocess_snv_count(self, group_id = "None", snv_count_path = snv_count_expected_location)
        self.assertEqual(snv_count, 21000)

if __name__ == '__main__':
    unittest.main()
