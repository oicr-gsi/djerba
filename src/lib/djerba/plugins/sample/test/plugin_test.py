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

class TestWgtsSamplePlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DIR'
        self.sup_dir = os.environ.get(sup_dir_var)
         
    def testWgtsSample(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/sample/report_json/sample.json")
        ini_location = os.path.join(self.sup_dir ,"plugins/sample/sample.ini") 

        params = {
            self.INI: ini_location,
            self.JSON: json_location,
            self.MD5: 'f23dbf3e5ac417740bcbb990723db0f0'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsSampleWithNA(self):
        """
        Purity, ploidy, callability, and coverage are NA
        """
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/sample/report_json/sample_na.json")
        ini_location = os.path.join(self.sup_dir ,"plugins/sample/sample_na.ini")

        params = {
            self.INI: ini_location,
            self.JSON: json_location,
            self.MD5: 'c9b5dd13be0f6d947550d93cd165b64f'
        }
        self.run_basic_test(test_source_dir, params)


if __name__ == '__main__':
    unittest.main()
