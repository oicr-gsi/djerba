#! /usr/bin/env python3

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

class TestReportTitle(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name

    def testClinicalTitle(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(test_source_dir, "clinical_title.json")

        params = {
            self.INI: 'clinical_title.ini',
            self.JSON: json_location,
            self.MD5: 'dcaa16f893c873d5a1382a340222c777'
        }
        self.run_basic_test(test_source_dir, params)

    def testFailedTitle(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(test_source_dir ,"failed_title.json")

        params = {
            self.INI: 'failed_title.ini',
            self.JSON: json_location,
            self.MD5: '924bbd63f2058d74856ec81244055271'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
