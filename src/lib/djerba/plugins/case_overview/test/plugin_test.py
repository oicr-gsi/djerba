#! /usr/bin/env python3

"""Test of the patient info plugin"""

import logging
import os
import string
import unittest
import tempfile
import djerba.core.constants as constants
from shutil import copy
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.validator import path_validator

class TestCaseOverview(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testCaseOverviewWGTS(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"case-overview-plugin/case_overview_WGTS.json")

        params = {
            self.INI: 'case_overview_WGTS.ini',
            self.JSON: json_location,
            self.MD5: 'f8763747e45463c8163a8fe6d6c1956a' # TO CHANGE
        }
        self.run_basic_test(test_source_dir, params)

    def testCaseOverviewTAR(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"case-overview-plugin/case_overview_TAR.json")

        params = {
            self.INI: 'case_overview_TAR.ini',
            self.JSON: json_location,
            self.MD5: 'f8763747e45463c8163a8fe6d6c1956a' # TO CHANGE
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
