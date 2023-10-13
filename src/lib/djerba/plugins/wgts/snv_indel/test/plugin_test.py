#! /usr/bin/env python3

"""
Test of the WGTS SNV/indel plugin
"""

import os
import unittest
import tempfile

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.wgts.snv_indel.plugin as snv_indel
from djerba.core.workspace import workspace

class TestWGTSsmallPlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testWGTSsmall(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"wgs-snv_indel-plugin/report_json/snv_indel.wgs.json")
        params = {
            self.INI: 'snv_indel.ini',
            self.JSON: json_location,
            self.MD5: '1a2eb6a3602abae40186e5aa4cfd77e0'
        }
        self.run_basic_test(test_source_dir, params)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['vaf_plot']:
            del data['plugins']['wgts.snv_indel']['results'][key]
        return data 

if __name__ == '__main__':
    unittest.main()
