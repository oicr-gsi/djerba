#! /usr/bin/env python3

"""
Test of the WGTS small plugin
AUTHOR: Felix Beaudry
"""

import os
import unittest
import tempfile
import string

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.wgts.cnv_purple.plugin as cnv
from djerba.core.workspace import workspace

class TestPurplePlugin(PluginTester):

    WGTS_INI_NAME = 'cnv.wgts.ini'
    WGS_INI_NAME = 'cnv.wgs.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def test_get_purple_purity(self):
        purple_purity_tsv = os.path.join(self.sup_dir ,"plugins/cnv-purple/purple.purity.tsv")
        observed_purity = cnv.get_purple_purity(purple_purity_tsv)
        self.assertEqual(observed_purity[0], 0.3)
        self.assertEqual(observed_purity[1], 5.3)

    def testWGTScnv(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.WGTS_INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.WGTS_INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/cnv-purple/report_json/cnv.purple.json")
        params = {
            self.INI: self.WGTS_INI_NAME,
            self.JSON: json_location,
            self.MD5: '4b32ff882773269118f45ba78770eaed'
        }
        self.run_basic_test(input_dir, params)

    def testWGScnv(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.WGS_INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.WGS_INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/cnv-purple/report_json/cnv.purple.json")
        params = {
            self.INI: self.WGS_INI_NAME,
            self.JSON: json_location,
            self.MD5: '4b32ff882773269118f45ba78770eaed'
        }
        self.run_basic_test(input_dir, params)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['cnv plot']:
            del data['plugins']['wgts.cnv_purple']['results'][key]
        return data 
    
if __name__ == '__main__':
    unittest.main()
