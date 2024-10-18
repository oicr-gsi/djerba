#! /usr/bin/env python3

"""Test of the failed report plugin"""

import os
import unittest
import tempfile
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.environment import directory_finder

class TestFailedReportPlugin(PluginTester):
    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()

    def testFailedReport(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = "failed_report.json"
        params = {
            self.INI: 'failed_report.ini',
            self.JSON: json_location,
            self.MD5: '416c14efbaec900ef37badad88955d7e'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
