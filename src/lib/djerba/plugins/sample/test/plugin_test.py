#! /usr/bin/env python3

"""
Test of the WGTS sample plugin
"""

import os
import unittest
import tempfile
import shutil
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.sample.plugin as sample
from djerba.core.workspace import workspace

class TestTarSamplePlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)
         
        self.sample_info_json = os.path.join(self.sup_dir, "wgts-sample-plugin/sample_info.json")

    def testTarSample(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"wgts-sample-plugin/report_json/sample.json")
        
        # Copy file into the temporary directory
        shutil.copy(self.sample_info_json, self.tmp_dir)

        params = {
            self.INI: 'sample.ini',
            self.JSON: json_location,
            self.MD5: '2564bbc00c738b4e2be0ef9ececb1e24'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
