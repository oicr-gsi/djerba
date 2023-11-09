#! /usr/bin/env python3

"""
Test of the pwgs plugin
AUTHOR: Felix Beaudry
"""

import os
import unittest
import tempfile
import shutil
import string
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.tar.sample.plugin as sample
from djerba.core.workspace import workspace

class TestTarSamplePlugin(PluginTester):
    
    INI_NAME = 'tar.sample.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testTarSample(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"tar-plugin/report_json/tar.sample.json")
                
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: 'eebb83aa8e6d8a01781e5736de5c8d21'
        }
        self.run_basic_test(input_dir, params)

    def test_process_ichor_json(self):
        ichor_expected_location = os.path.join(self.sup_dir ,"tar-plugin/ichorCNA_metrics.json")
        ichor_json = sample.main.process_ichor_json(self, ichor_expected_location)
        purity = ichor_json["tumor_fraction"]
        self.assertEqual(purity, 0.03978)

    def test_process_consensus_cruncher_Pl(self):
        cc_expected_location = os.path.join(self.sup_dir ,"tar-plugin/allUnique-hsMetrics.HS.Pl.txt")
        unique_coverage = sample.main.process_consensus_cruncher(self, cc_expected_location)
        self.assertEqual(unique_coverage, 2088)
    
    def test_process_consensus_cruncher_BC(self):
        cc_expected_location = os.path.join(self.sup_dir ,"tar-plugin/allUnique-hsMetrics.HS.BC.txt")
        collapsed_coverage_bc = sample.main.process_consensus_cruncher(self, cc_expected_location)
        self.assertEqual(collapsed_coverage_bc, 910)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['files']:
            del data['plugins']['tar.sample']['results'][key]
        return data

if __name__ == '__main__':
    unittest.main()
