#! /usr/bin/env python3

"""
Test of the snv_indel plugin
"""

import os
import unittest
import tempfile
import shutil
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.tar.snv_indel.plugin as snv_indel
from djerba.core.workspace import workspace

class TestTarSNVIndelPlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

        self.provenance_output = os.path.join(self.sup_dir, "swgs-plugin/provenance_subset.tsv.gz")
        self.purity_pass = os.path.join(self.sup_dir, "swgs-plugin/purity_pass/purity.txt")
        self.purity_fail = os.path.join(self.sup_dir, "swgs-plugin/purity_fail/purity.txt")
        self.purity_pass_json = os.path.join(self.sup_dir, "swgs-plugin/purity_pass/tar_swgs_purity_pass.json")
        self.purity_fail_json = os.path.join(self.sup_dir, "swgs-plugin/purity_fail/tar_swgs_purity_fail.json")

    def testTarSNVIndelPurityPass(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        # Copy files into the temporary directory
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.purity_pass, self.tmp_dir)
        json_location = os.path.join(self.sup_dir ,"swgs-plugin/purity_pass/tar_swgs_purity_pass.json")

        params = {
            self.INI: 'data/tar_swgs.ini',
            self.JSON: json_location,
            self.MD5: 'f88f2a6a4178d13889b2e352eda3c77d'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarSNVIndelPurityFail(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.purity_fail, self.tmp_dir)
        json_location = os.path.join(self.sup_dir ,"swgs-plugin/purity_fail/tar_swgs_purity_fail.json")

        params = {
            self.INI: 'data/tar_swgs.ini',
            self.JSON: json_location,
            self.MD5: '04c1dc596af728ae780767d8cf918c2b'
        }
        self.run_basic_test(test_source_dir, params)
    
    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        del data['plugins']['tar.swgs']['results']['cnv_plot']
        return data 

if __name__ == '__main__':
    unittest.main()
