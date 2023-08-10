#! /usr/bin/env python3

"""
Test of the pwgs plugin
AUTHOR: Felix Beaudry
"""

import os
import unittest
import tempfile

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.tar.sample.plugin as sample
from djerba.core.workspace import workspace
from djerba.snv_indel_tools.preprocess import preprocess

class TestTarSamplePlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def test_process_ichor_json(self):
        ichor_expected_location = os.path.join(self.sup_dir ,"tar-plugin/ichorCNA_metrics.json")
        ichor_json = sample.main.process_ichor_json(self, ichor_expected_location)
        purity = ichor_json["tumor_fraction"]
        self.assertEqual(purity, 0.03978)

    def test_process_croncensus_cruncher(self):
        cc_expected_location = os.path.join(self.sup_dir ,"tar-plugin/allUnique-hsMetrics.HS.txt")
        unique_coverage = sample.main.process_croncensus_cruncher(self, cc_expected_location)
        self.assertEqual(unique_coverage, 2088)

if __name__ == '__main__':
    unittest.main()
