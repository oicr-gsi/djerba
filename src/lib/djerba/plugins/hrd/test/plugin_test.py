#! /usr/bin/env python3

"""Test of the pwgs plugin"""

import os
import unittest
import tempfile
import string

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.hrd.plugin as hrd
from djerba.core.workspace import workspace

class TestPwgAnalysisPlugin(PluginTester):

    INI_NAME = 'test.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testHRD(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/hrd/report_json/hrd.djerba.json")
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '1007ef73d0442342d7ccfac539f38cf8'
        }
        self.run_basic_test(input_dir, params)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['files','hrd_base64']:
            del data['plugins']['hrd']['results'][key]
        return data        

if __name__ == '__main__':
    unittest.main()
