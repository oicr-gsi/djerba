#! /usr/bin/env python3

import os
import unittest
import tempfile
import shutil
import string
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.core.workspace import workspace

class TestTarSwgsPlugin(PluginTester):

    INI_NAME = 'tar_swgs.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DIR'
        self.sup_dir = os.environ.get(sup_dir_var)

        self.provenance_output = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/provenance_subset.tsv.gz")
        self.purity_pass = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/purity_pass/purity.txt")
        self.purity_fail = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/purity_fail/purity.txt")
        self.purity_pass_json = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/purity_pass/tar_swgs_purity_pass.json")
        self.purity_fail_json = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/purity_fail/tar_swgs_purity_fail.json")

    def testTarSwgsPurityPass(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        # Copy files into the temporary directory
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

        json_location = os.path.join(self.sup_dir ,"plugins/tar/tar-cnv/purity_pass/tar_swgs_purity_pass.json")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: 'a19eb70301cc188ce297c8e484c124a8'
        }
        self.run_basic_test(input_dir, params)

    def testTarSwgsPurityFail(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.purity_fail, self.tmp_dir)
        
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)

        json_location = os.path.join(self.sup_dir ,"plugins/tar/tar-cnv/purity_fail/tar_swgs_purity_fail.json")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '48f7c78a19120456ee1c446ac67f5c33'
        }
        self.run_basic_test(input_dir, params)
    
if __name__ == '__main__':
    unittest.main()
