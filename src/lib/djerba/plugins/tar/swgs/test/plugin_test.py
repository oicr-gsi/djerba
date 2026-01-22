#! /usr/bin/env python3

import os
import unittest
import tempfile
import shutil
import string
from copy import deepcopy
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.core.workspace import workspace
from djerba.util.environment import directory_finder

class TestTarSwgsPlugin(PluginTester):

    INI_NAME = 'tar_swgs.ini'

    def setUp(self):
        super().setUp()
        # superlcass sets path_validator, tmp_dir
        # set maxDiff locally so we can override
        #self.path_validator = path_validator()
        #self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        #self.tmp_dir = self.tmp.name
        self.maxDiff = None
        self.sup_dir = directory_finder().get_test_dir()

        self.provenance_output = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/provenance_subset.tsv.gz")
        self.purity_pass = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/purity_pass/purity.txt")
        self.purity_fail = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/purity_fail/purity.txt")
        self.purity_pass_json = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/purity_pass/tar_swgs_purity_pass.json")
        self.purity_fail_json = os.path.join(self.sup_dir, "plugins/tar/tar-cnv/purity_fail/tar_swgs_purity_fail.json")

    def redact_json_data(self, data):
        redacted = deepcopy(data)
        # do not redact if empty
        if 'gene_information_merger' in redacted['merge_inputs']:
            redacted['merge_inputs']['gene_information_merger'] = self.PLACEHOLDER
        return redacted

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
        if not os.path.isdir(input_dir):
            os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)

        json_location = os.path.join(self.sup_dir ,"plugins/tar/tar-cnv/purity_pass/tar_swgs_purity_pass.json")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '0c1cd57b50dc4b69f20cef6a3a732026'
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
        if not os.path.isdir(input_dir):
            os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)

        json_location = os.path.join(self.sup_dir ,"plugins/tar/tar-cnv/purity_fail/tar_swgs_purity_fail.json")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: 'c9a2bfa63dc67c0ca3b9d23126d108df'
        }
        self.run_basic_test(input_dir, params)
    
if __name__ == '__main__':
    unittest.main()
