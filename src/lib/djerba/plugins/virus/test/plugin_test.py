#! /usr/bin/env python3

"""
Test for VIRUSBreakend plugin.
"""

import os
import unittest
import tempfile
import string
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.environment import directory_finder

class testVirus(PluginTester):

    INI_NAME = 'virus.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()
        self.json = os.path.join(self.sup_dir, "plugins/virus/virus.json")

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)

        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.json,
            self.MD5: '8188c77f8f36a222a61b0a76c2ddecc0'
        }
        self.run_basic_test(input_dir, params)

if __name__ == '__main__':
    unittest.main()
