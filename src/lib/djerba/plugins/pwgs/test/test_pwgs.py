#! /usr/bin/env python3

"""Test of the pwgs plugin"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.pwgs.analysis.plugin as analysis

class TestPwgsPlugins(PluginTester):

    def testPwgsAnalysis(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'data/pwgs.analysis.ini',
            self.JSON: 'data/report/pwgs.analysis.json',
            self.MD5: '28cc6bd2bbc66103a4bf0f6656a989e7'
        }
        self.run_basic_test(test_source_dir, params)

    def testPreprocessHbc(self):
        hbc_result = analysis.main.preprocess_hbc(self,'/.mounts/labs/CGI/scratch/fbeaudry/reporting/djerba/src/lib/djerba/plugins/pwgs/test/data/report/HBCs.csv')
        self.assertEqual(hbc_result['sites_checked'], 123616)
        self.assertEqual(hbc_result['hbc_n'], 24)

    def testPreprocessvaf(self):
        reads_detected = analysis.main.preprocess_vaf(self,'/.mounts/labs/CGI/scratch/fbeaudry/reporting/djerba/src/lib/djerba/plugins/pwgs/test/data/report/mrdetect.vaf.txt')
        self.assertEqual(reads_detected, 9241)

    def testPreprocessResults(self):
        results = analysis.main.preprocess_results(self,'/.mounts/labs/CGI/scratch/fbeaudry/reporting/djerba/src/lib/djerba/plugins/pwgs/test/data/report/mrdetect.txt')
        self.assertEqual(results['TF'], 0.0321 )
        self.assertEqual(results['pvalue'], 1.903e-05)
        self.assertEqual(results['outcome'], 'POSITIVE')
        self.assertEqual(results['significance_text'], 'significantly larger')

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['pwgs_base64']:
            del data['plugins']['pwgs.analysis']['results'][key]
        return data        

if __name__ == '__main__':
    unittest.main()
