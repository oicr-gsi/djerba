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
 
        self.provenance_output = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/swgs-plugin/provenance_subset.tsv.gz'
        self.purity_pass = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/swgs-plugin/purity_pass/purity.txt'
        self.purity_fail = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/swgs-plugin/purity_fail/purity.txt'
        self.purity_pass_json = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/swgs-plugin/purity_pass/tar_swgs_purity_pass.json'
        self.purity_fail_json = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/swgs-plugin/purity_fail/tar_swgs_purity_fail.json'
        
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testTarSNVIndelPurityPass(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        # Copy files into the temporary directory
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.purity_pass, self.tmp_dir)
        #json_location = os.path.join(self.sup_dir ,"swgs-plugin/purity_pass/tar_swgs.json")
        json_location = self.purity_pass_json

        params = {
            self.INI: 'data/tar_swgs.ini',
            self.JSON: json_location,
            self.MD5: 'e270143e36e38c272826fdd3ea4c6bea'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarSNVIndelPurityFail(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.purity_fail, self.tmp_dir)
        #json_location = os.path.join(self.sup_dir ,"swgs-plugin/purity_fail/tar_swgs.json")
        json_location = self.purity_fail_json

        params = {
            self.INI: 'data/tar_swgs.ini',
            self.JSON: json_location,
            self.MD5: '09a28d07a482dd121770c25a9bb5e252'
        }
        self.run_basic_test(test_source_dir, params)
    
    #def redact_json_data(self, data):
    #    """replaces empty method from testing.tools"""
    #    for key in ['cnv_plot']:
    #        del data['plugins']['tar.swgs']['results'][key]
    #    return data 

if __name__ == '__main__':
    unittest.main()
