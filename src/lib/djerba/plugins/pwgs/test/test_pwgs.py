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
            self.MD5: '6551a01ab07ef6f60a0b0b4ff5c46cad'
        }
        self.run_basic_test(test_source_dir, params)

    def testPreprocessHbc(self):
        hbc_result = analysis.preprocess_files.preprocess_hbc('/.mounts/labs/CGI/scratch/fbeaudry/reporting/djerba/src/lib/djerba/plugins/pwgs/test/data/report/HBCs.csv')
        self.assertEqual(hbc_result['sites_checked'], 19997)
        self.assertEqual(hbc_result['hbc_n'], 24)

    def testPreprocessvaf(self):
        reads_detected = analysis.preprocess_files.preprocess_vaf('/.mounts/labs/CGI/scratch/fbeaudry/reporting/djerba/src/lib/djerba/plugins/pwgs/test/data/report/mrdetect.vaf.txt')
        self.assertEqual(reads_detected,11362)

    def testPreprocessResults(self):
        results = analysis.preprocess_files.preprocess_results('/.mounts/labs/CGI/scratch/fbeaudry/reporting/djerba/src/lib/djerba/plugins/pwgs/test/data/report/mrdetect.txt')
        self.assertEqual(results['TF'], 0)
        self.assertEqual(results['pvalue'], 0.590773060500315)
        self.assertEqual(results['outcome'], 'FALSE')
        self.assertEqual(results['significance_text'], 'not significantly different')

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['pwgs_base64']:
            del data['plugins']['pwgs.analysis']['results'][key]
        return data        

if __name__ == '__main__':
    unittest.main()
