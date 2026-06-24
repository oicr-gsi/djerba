#! /usr/bin/env python3

"""Test of the pwgs plugin"""

import os
import unittest
import tempfile
import string
import shutil

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.core.workspace import workspace
import djerba.plugins.pwgs.constants as constants
import djerba.plugins.pwgs.analysis.plugin as analysis
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools
from djerba.util.environment import directory_finder

class TestPwgAnalysisPlugin(PluginTester):

    INI_NAME = 'pwgs.analysis.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()

    def testPreprocessHbc(self):
        hbc_expected_location = os.path.join(self.sup_dir ,"plugins/pwgs/HBCs.csv")
        hbc_result = analysis.main.preprocess_hbc(self, hbc_expected_location)
        self.assertEqual(hbc_result[constants.SITES_CHECKED], 123616)
        self.assertEqual(hbc_result[constants.COHORT_N], 24)

    def testPreprocessvaf(self):
        vaf_expected_location = os.path.join(self.sup_dir ,"plugins/pwgs/mrdetect.vaf.txt")
        reads_detected = analysis.main.preprocess_vaf(self, vaf_expected_location)
        self.assertEqual(reads_detected, 18768)

    def testPreprocessResults(self):
        results_expected_location = os.path.join(self.sup_dir ,"plugins/pwgs/mrdetect.txt")
        results = pwgs_tools.preprocess_results(self, results_expected_location)
        self.assertEqual(results[constants.TUMOUR_FRACTION_ZVIRAN], 0.016 )
        self.assertEqual(results[constants.PVALUE], 1.903e-05)
        self.assertEqual(results[constants.CTDNA_OUTCOME], 'DETECTED')
        self.assertEqual(results[constants.SIGNIFICANCE], 'significantly larger')

    def test_pwgs_analysis_exists(self):
        # test the scenario where pWGS_case_overview_output.json exist
        shutil.copyfile(os.path.join(self.sup_dir, f"plugins/pwgs/report_json/pwgs.case.json"), os.path.join(self.get_tmp_dir(), "pWGS_case_overview_output.json"))
        self.run_test_with_scenario("pwgs.analysis.file.exists.scenario.json", "713518f5ff66b6d2b72df5f53f9f8b61")

    def test_pwgs_analysis_not_exists(self):
        # test the scenario where pWGS_case_overview_output.json doesn't exist
        self.run_test_with_scenario("pwgs.analysis.file.doesnt.exist.scenario.json", "579bb1ad12226ff0347b9f62b79c5fce")

    def run_test_with_scenario(self, json_filename, md5_checksum):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)

        json_location = os.path.join(self.sup_dir, f"plugins/pwgs/report_json/{json_filename}")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: md5_checksum
        }
        self.run_basic_test(input_dir, params)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        del data['results']['pwgs_base64']
        return data        

if __name__ == '__main__':
    unittest.main()
