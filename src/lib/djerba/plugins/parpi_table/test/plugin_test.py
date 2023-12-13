#! /usr/bin/env python3

"""Test of the PARPi table plugin"""

import os
import unittest
import tempfile
import string
import shutil
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.core.workspace import workspace

class TestParpiTablePlugin(PluginTester):

    INI_NAME = 'test.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

        self.data_CNA = os.path.join(self.sup_dir, "plugins/parpi_table/data_CNA.txt")
        self.data_mutations = os.path.join(self.sup_dir, "plugins/parpi_table/data_mutations_extended.txt")
        self.data_expression = os.path.join(self.sup_dir, "plugins/parpi_table/data_expression_percentile_tcga.txt")

    def testParpiTable(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.data_CNA, self.tmp_dir)
        shutil.copy(self.data_mutations, self.tmp_dir)
        shutil.copy(self.data_expression, self.tmp_dir)

        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/parpi_table/report.json")
        params = {
            self.INI: 'input/' + self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '667f996b2b3fc2a0dd8c1278c30a074f'
        }
        self.run_basic_test(self.tmp_dir, params)

if __name__ == '__main__':
    unittest.main()
