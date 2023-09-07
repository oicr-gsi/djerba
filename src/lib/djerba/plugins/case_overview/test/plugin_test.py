#! /usr/bin/env python3

"""Test of the patient info plugin"""

import logging
import os
import string
import unittest
import djerba.core.constants as constants
from shutil import copy
from djerba.plugins.plugin_tester import PluginTester
import tempfile
from djerba.util.validator import path_validator
from djerba.core.workspace import workspace

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
            self.INI: 'data/case_overview_WGTS.ini',
            self.JSON: json_location,
            self.MD5: 'f8763747e45463c8163a8fe6d6c1956a' # TO CHANGE
        }
        self.run_basic_test(test_source_dir, params)

    def testCaseOverviewTAR(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"case-overview-plugin/case_overview_TAR.json")

        params = {
            self.INI: 'data/case_overview_TAR.ini',
            self.JSON: json_location,
            self.MD5: 'f8763747e45463c8163a8fe6d6c1956a' # TO CHANGE
        }
        self.run_basic_test(test_source_dir, params)



    #def test(self):
    #    # customize the INI file with path to provenance input
    #    # then copy INI and JSON files to the tmp directory and run the basic test
    #    data_dir_root = os.getenv(constants.DJERBA_TEST_DIR_VAR)
    #    data_dir = os.path.join(data_dir_root, constants.PLUGINS, 'case_overview')
    #    provenance_path = os.path.join(data_dir, 'provenance_subset.tsv.gz')
    #    test_source_dir = os.path.realpath(os.path.dirname(__file__))
    #    with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
    #        template_str = in_file.read()
    #    template = string.Template(template_str)
    #    ini_str = template.substitute({'FPR_PATH': provenance_path})
    #    input_dir = os.path.join(self.get_tmp_dir(), 'input')
    #    os.mkdir(input_dir)
    #    with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
    #        ini_file.write(ini_str)
    #    copy(os.path.join(test_source_dir, self.JSON_NAME), input_dir)
    #    params = {
    #        self.INI: self.INI_NAME,
    #        self.JSON: self.JSON_NAME,
    #        self.MD5: '2fb2aa2c015b46c5d6c35a4399dbb4e6'
    #    }
    #    self.run_basic_test(input_dir, params, 'case_overview', logging.ERROR)

if __name__ == '__main__':
    unittest.main()

