#! /usr/bin/env python3

"""
Test of the genomic_landscape plugin
"""

import os
import unittest
import tempfile
import shutil
import string
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.core.workspace import workspace
from djerba.util.environment import directory_finder

class TestGenomicLandscapePlugin(PluginTester):
    
    INI_NAME = 'genomic_landscape.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()
        
        self.data_mut_ex = os.path.join(self.sup_dir, "plugins/genomic-landscape/data_mutations_extended.txt")
        self.data_seg = os.path.join(self.sup_dir, "plugins/genomic-landscape/data.seg")
        self.sample_info = os.path.join(self.sup_dir, "plugins/genomic-landscape/sample_info.json")

    def testGenomicLandscapeLowTmbStableMsi(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.data_mut_ex, self.tmp_dir)
        shutil.copy(self.data_seg, self.tmp_dir)
        shutil.copy(self.sample_info, self.tmp_dir)

        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)

        json_location = os.path.join(self.sup_dir ,"plugins/genomic-landscape/report_json/genomic_landscape.json")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '9ce53bdd5883af1d8b515187b7aa7e98'
        }
        self.run_basic_test(input_dir, params)

if __name__ == '__main__':
    unittest.main()
