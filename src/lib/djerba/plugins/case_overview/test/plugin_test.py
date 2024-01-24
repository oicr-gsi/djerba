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

import sys

class TestCaseOverview(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)
        self.sample_json = os.path.join(self.sup_dir, "plugins/case_overview/sample_info.json")

    def testCaseOverviewWGTS(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/case_overview/case_overview_WGTS.json")
        print(json_location, file=sys.stderr)
        shutil.copy(self.sample_json, self.tmp_dir)

        params = {
            self.INI: 'case_overview_WGTS.ini',
            self.JSON: json_location,
            self.MD5: '98420eb4576d80fd2944788973c9cb32'
        }
        self.run_basic_test(test_source_dir, params)

    def SKIPtestCaseOverviewTAR(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/case_overview/case_overview_TAR.json")
        print(json_location, file=sys.stderr)
        params = {
            self.INI: 'case_overview_TAR.ini',
            self.JSON: json_location,
            self.MD5: '06d2aa02f67915c9a2f8a9eb1815735e'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
