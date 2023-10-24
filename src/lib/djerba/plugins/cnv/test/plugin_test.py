#! /usr/bin/env python3

"""
Test of the WGTS CNV plugin
"""

import os
import string
import tempfile
import unittest
from shutil import copy
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.plugins.cnv.plugin import main as cnv
from djerba.core.workspace import workspace

class TestWgtsCnv(PluginTester):

    INI_NAME = 'cnv.ini'
    JSON_NAME = 'cnv.json'

    def testWgtsCnv(self):
        sup_dir = os.environ.get('DJERBA_TEST_DATA')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        sequenza_filename = 'PANX_1391_Lv_M_WG_100-NH-020_LCM3_results.test.zip'
        sequenza_path = os.path.join(sup_dir, 'plugins', 'cnv', sequenza_filename)
        expression_filename = 'data_expression_percentile_tcga.json'
        expression_path = os.path.join(sup_dir, 'plugins', 'cnv', expression_filename)
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'SEQUENZA_PATH': sequenza_path})
        tmp_dir = self.get_tmp_dir()
        input_dir = os.path.join(tmp_dir, 'input')
        os.mkdir(input_dir)
        work_dir = os.path.join(tmp_dir, 'work')
        os.mkdir(work_dir)
        copy(expression_path, work_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(os.path.join(test_source_dir, self.JSON_NAME), input_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: os.path.join(sup_dir, 'plugins', 'cnv', self.JSON_NAME),
            self.MD5: '317e76fb2baeb7149652ec5782622e79'
        }
        self.run_basic_test(input_dir, params, work_dir=work_dir)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        del data['plugins']['cnv']['results']['cnv plot']
        return data 

if __name__ == '__main__':
    unittest.main()
