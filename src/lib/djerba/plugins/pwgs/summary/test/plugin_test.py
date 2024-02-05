#! /usr/bin/env python3

"""Test of the pwgs plugin"""

import os
import unittest
import tempfile
import string

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.pwgs.analysis.plugin as analysis
import djerba.plugins.pwgs.sample.plugin as sample
import djerba.plugins.pwgs.pwgs_tools as pwgs_tools
from djerba.core.workspace import workspace
import djerba.plugins.pwgs.constants as constants
from djerba.util.environment import directory_finder

class TestPwgSamplePlugin(PluginTester):

    INI_NAME = 'pwgs.summary.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()

    def testPwgsSummary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/pwgs/report_json/pwgs.summary.json")
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '6416078989efc8197eb5179ebf379614'
        }
        self.run_basic_test(input_dir, params)


if __name__ == '__main__':
    unittest.main()
