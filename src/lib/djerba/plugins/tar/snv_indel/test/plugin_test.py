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
        
 
        self.data_CNA = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/snv-indel-plugin/data_CNA.txt'
        self.data_CNA_onco = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/snv-indel-plugin/data_CNA_oncoKBgenes_nonDiploid.txt'
        self.provenance_output = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/snv-indel-plugin/provenance_subset.tsv.gz'
        self.json = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/snv-indel-plugin/tar_snv_indel.json'
        

        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testTarSNVIndel(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        # Copy files into the temporary directory
        shutil.copy(self.data_CNA, self.tmp_dir)
        shutil.copy(self.data_CNA_onco, self.tmp_dir)
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.json, self.tmp_dir)

        json_location = self.json
        params = {
            self.INI: 'data/tar_snv_indel.ini',
            self.JSON: json_location,
            self.MD5: '83b3c4efcae494cb41c6b2717dd814fb'
        }
        self.run_basic_test(test_source_dir, params)


if __name__ == '__main__':
    unittest.main()
