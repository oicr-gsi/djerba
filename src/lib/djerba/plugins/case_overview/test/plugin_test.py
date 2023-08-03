#! /usr/bin/env python3

"""Test of the patient info plugin"""

import logging
import os
import string
import unittest
import djerba.core.constants as constants
from shutil import copy
from djerba.plugins.plugin_tester import PluginTester

class TestCaseOverview(PluginTester):

    INI_NAME = 'case_overview.ini'
    JSON_NAME = 'case_overview.json'

    def test(self):
        # customize the INI file with path to provenance input
        # then copy INI and JSON files to the tmp directory and run the basic test
        data_dir_root = os.getenv(constants.DJERBA_TEST_DIR_VAR)
        data_dir = os.path.join(data_dir_root, constants.PLUGINS, 'case_overview')
        provenance_path = os.path.join(data_dir, 'provenance_subset.tsv.gz')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'FPR_PATH': provenance_path})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(os.path.join(test_source_dir, self.JSON_NAME), input_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME,
            self.MD5: '8b44b4f31d9c2efb2be71968d0d1fe7a'
        }
        self.run_basic_test(input_dir, params, 'case_overview', logging.ERROR)

if __name__ == '__main__':
    unittest.main()

