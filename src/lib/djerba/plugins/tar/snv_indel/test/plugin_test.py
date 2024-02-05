#! /usr/bin/env python3

import os
import unittest
import tempfile
import shutil
import string
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.tar.snv_indel.plugin as snv_indel
from djerba.core.workspace import workspace
from djerba.util.environment import directory_finder

class TestTarSNVIndelPlugin(PluginTester):
    
    INI_NAME = 'tar_snv_indel.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()
        
        self.data_CNA = os.path.join(self.sup_dir, "plugins/tar/tar-snv-indel/data_CNA.txt")
        self.provenance_output = os.path.join(self.sup_dir, "plugins/tar/tar-snv-indel/provenance_subset.tsv.gz")
        self.purity_pass = os.path.join(self.sup_dir, "plugins/tar/tar-snv-indel/purity_pass/purity.txt")
        self.purity_fail = os.path.join(self.sup_dir, "plugins/tar/tar-snv-indel/purity_fail/purity.txt")
        self.purity_pass_json = os.path.join(self.sup_dir, "plugins/tar/tar-snv-indel/purity_pass/tar_snv_indel_purity_pass.json")
        self.purity_fail_json = os.path.join(self.sup_dir, "plugins/tar/tar-snv-indel/purity_fail/tar_snv_indel_purity_fail.json")

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

        json_location = os.path.join(self.sup_dir ,"plugins/tar/tar-snv-indel/purity_fail/tar_snv_indel_purity_fail.json")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '4a6ecfc672265f9ce9e13bd1674f0969'
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

        json_location = os.path.join(self.sup_dir ,"plugins/tar/tar-snv-indel/purity_pass/tar_snv_indel_purity_pass.json")
        
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: 'c645d99817ef63d1e8d048534de14060'
        }
        self.run_basic_test(input_dir, params)

if __name__ == '__main__':
    unittest.main()
