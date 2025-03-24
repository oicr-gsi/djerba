#! /usr/bin/env python3

import os
import unittest
import tempfile
import string
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.environment import directory_finder


class TestHLAPlugin(PluginTester):
    INI_NAME = 'hla.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()
        # Expected output file
        self.json = os.path.join(self.sup_dir, "plugins", "hla", "GSICAPBENCH_1391_Ly_R_HLA_alleles.json")

    def testHLAPlugin(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})

        # Create the input subdirectory and write the INI file there.
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        ini_file_path = os.path.join(input_dir, self.INI_NAME)
        with open(ini_file_path, 'w') as ini_file:
            ini_file.write(ini_str)

        params = {
            self.INI: os.path.join('input', self.INI_NAME),
            self.JSON: self.json,
            self.MD5: 'd9c55683253d6a4a97140133aab46880'
        }
        self.run_basic_test(self.tmp_dir, params)


if __name__ == '__main__':
    unittest.main()
