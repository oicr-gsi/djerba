#! /usr/bin/env python3

"""
Test of the WGTS small plugin
AUTHOR: Felix Beaudry
"""

import os
import unittest
import tempfile

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.wgts.cnv.plugin as cnv
from djerba.core.workspace import workspace

class TestWGTSsmallPlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testWGTScnv(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"cnv-plugin/report_json/cnv.wgs.json")
        params = {
            self.INI: 'cnv.ini',
            self.JSON: json_location,
            self.MD5: 'e8d5c9777e4dbd6162105cd189cb40bf'
        }
        self.run_basic_test(test_source_dir, params)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        for key in ['cnv_plot']:
            del data['plugins']['wgts.cnv']['results'][key]
        return data 

if __name__ == '__main__':
    unittest.main()
