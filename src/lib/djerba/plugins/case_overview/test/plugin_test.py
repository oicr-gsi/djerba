#! /usr/bin/env python3

"""Test of the case overview plugin"""

import os
import shutil
import logging
import string
import unittest
import tempfile
import djerba.core.constants as constants
from shutil import copy
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.validator import path_validator
from djerba.util.environment import directory_finder

class TestCaseOverview(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()
        self.sample_json = os.path.join(self.sup_dir, "plugins/case_overview/sample_info.json")

    def testCaseOverviewWGTS(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/case_overview/case_overview_WGTS.json")
        shutil.copy(self.sample_json, self.tmp_dir)

        params = {
            self.INI: 'case_overview_WGTS.ini',
            self.JSON: json_location,
            self.MD5: '09bf73811c265362e010a92e1d833de5'
        }
        self.run_basic_test(test_source_dir, params)

    def testCaseOverviewTAR(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/case_overview/case_overview_TAR.json")
        params = {
            self.INI: 'case_overview_TAR.ini',
            self.JSON: json_location,
            self.MD5: '1a32247a76f34ff50efe5e4ae98dfea4'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
