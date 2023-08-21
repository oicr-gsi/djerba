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
        self.purity = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/swgs-plugin/purity.txt'
        self.json = '/.mounts/labs/CGI/scratch/aalam/plugin_tests/swgs-plugin/tar_swgs.json'
        

        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testTarSNVIndel(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        # Copy files into the temporary directory
        shutil.copy(self.provenance_output, self.tmp_dir)
        shutil.copy(self.purity, self.tmp_dir)

        json_location = self.json
        params = {
            self.INI: 'data/tar_swgs.ini',
            self.JSON: json_location,
            self.MD5: 'cb472dc9ec3dacfcd8ada05fe687fe1c'
        }
        self.run_basic_test(test_source_dir, params)


if __name__ == '__main__':
    unittest.main()
