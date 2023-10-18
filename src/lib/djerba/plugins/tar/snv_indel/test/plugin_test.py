#! /usr/bin/env python3

"""
Test of the snv_indel plugin
"""

import os
import unittest
import tempfile
import shutil
import string
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.tar.snv_indel.plugin as snv_indel
from djerba.core.workspace import workspace

class TestTarSNVIndelPlugin(PluginTester):
    
    INI_NAME = 'tar_snv_indel.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)
        
        self.data_CNA = os.path.join(self.sup_dir, "snv-indel-plugin/data_CNA.txt")
        self.provenance_output = os.path.join(self.sup_dir, "snv-indel-plugin/provenance_subset.tsv.gz")
        self.purity_pass = os.path.join(self.sup_dir, "snv-indel-plugin/purity_pass/purity.txt")
        self.purity_fail = os.path.join(self.sup_dir, "snv-indel-plugin/purity_fail/purity.txt")
        self.purity_pass_json = os.path.join(self.sup_dir, "snv-indel-plugin/purity_pass/tar_snv_indel_purity_pass.json")
        self.purity_fail_json = os.path.join(self.sup_dir, "snv-indel-plugin/purity_fail/tar_snv_indel_purity_fail.json")

    def testTarSNVIndelPurityFail(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.data_CNA, self.tmp_dir)
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.purity_fail, self.tmp_dir)
        shutil.copy(self.purity_fail, self.tmp_dir)
        
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)

        json_location = os.path.join(self.sup_dir ,"snv-indel-plugin/purity_fail/tar_snv_indel_purity_fail.json")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '870394bc5ddad8afa1c8a3c88dd12601'
        }
        self.run_basic_test(input_dir, params)

    def testTarSNVIndelPurityPass(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.data_CNA, self.tmp_dir)
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.purity_pass, self.tmp_dir)
        
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)

        json_location = os.path.join(self.sup_dir ,"snv-indel-plugin/purity_pass/tar_snv_indel_purity_pass.json")
        
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '30a4bc52e66b84424faa6abf045e1557'
        }
        self.run_basic_test(input_dir, params)

if __name__ == '__main__':
    unittest.main()
