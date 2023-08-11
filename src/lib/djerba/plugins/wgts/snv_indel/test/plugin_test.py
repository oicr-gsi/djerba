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
import djerba.plugins.wgts.snv_indel.plugin as snv_indel
from djerba.core.workspace import workspace

class TestWGTSsmallPlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testWGTSsmall(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"snv_indel-plugin/report_json/snv_indel.wgs.json")
        params = {
            self.INI: 'snv_indel.ini',
            self.JSON: json_location,
            self.MD5: '385f7b5ec83595a37ea60328b5e28358'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
