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
from djerba.util.environment import directory_finder

class TestWgtsSamplePlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()
        
    def testWgtsSample(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/sample/report_json/sample.json")
        ini_location = os.path.join(self.sup_dir ,"plugins/sample/sample.ini") 

        params = {
            self.INI: ini_location,
            self.JSON: json_location,
            self.MD5: '8d21df38bbfdba551e86b41adf1f0381'
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
            self.MD5: 'f0d700a1c983b42637a328c08097add6'
        }
        self.run_basic_test(test_source_dir, params)


if __name__ == '__main__':
    unittest.main()
