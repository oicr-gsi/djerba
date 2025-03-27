#! /usr/bin/env python3

"""Test of the provenance helper"""

import logging
import os
import unittest
from configparser import ConfigParser
from shutil import copy
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.environment import directory_finder
from djerba.util.testing.tools import TestBase
import djerba.core.constants as cc

class TestExpressionHelper(TestBase):

    CORE = 'core'
    HELPER_NAME = 'expression_helper'

    def test_configure(self):
        cp = ConfigParser()
        cp.add_section(self.CORE)
        cp.set(self.CORE, 'project', 'PASS01')
        cp.set(self.CORE, 'donor', 'PANX_1500')
        cp.add_section(self.HELPER_NAME)
        cp.set(self.HELPER_NAME, 'tcga_code', 'PAAD')
        loader = helper_loader(logging.ERROR)
        work_dir = self.tmp_dir
        finder = directory_finder()
        data_dir = finder.get_data_dir()
        test_dir = os.path.join(finder.get_test_dir(), 'helpers', 'expression')
        sample_info = os.path.join(test_dir, 'sample_info.json')
        fpr = os.path.join(test_dir, 'provenance_subset.tsv.gz')
        copy(sample_info, work_dir)
        copy(fpr, work_dir)
        ws = workspace(work_dir)
        helper_main = loader.load(self.HELPER_NAME, ws)
        config = helper_main.configure(cp)
        plugin_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) # go 2 directories up
        configured_enscon = config.get(self.HELPER_NAME, helper_main.ENSCON_KEY)
        self.assertTrue(os.path.exists(configured_enscon))
        tcga_code = config.get(self.HELPER_NAME, helper_main.TCGA_CODE_KEY)
        self.assertEqual(tcga_code, 'PAAD')
        # path was derived from file provenance subset, should not change
        rsem = config.get(self.HELPER_NAME, helper_main.RSEM_GENES_RESULTS_KEY)
        self.assertEqual(self.getMD5_of_string(rsem), '6adf97f83acf6453d4a6a4b1070f3754')
        # check the reference path
        found = config.get(self.HELPER_NAME, helper_main.GEP_REFERENCE_KEY)
        expected = '/.mounts/labs/CGI/gsi/tools/djerba/gep_reference.txt.gz'
        self.assertEqual(found, expected)

    def test_extract(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        cp = ConfigParser()
        cp.read(os.path.join(test_source_dir, 'config.ini'))
        finder = directory_finder()
        test_data_dir = os.path.join(finder.get_test_dir(), 'helpers', 'expression')
        loader = helper_loader(logging.WARNING)
        ws = workspace(self.tmp_dir)
        helper_main = loader.load(self.HELPER_NAME, ws)
        # configure the INI
        plugin_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) # go 2 directories up
        enscon = os.path.join(plugin_dir, 'ensemble_conversion_hg38.txt')
        cp.set(self.HELPER_NAME, helper_main.ENSCON_KEY, enscon)
        rsem = os.path.join(test_data_dir, 'PANX_1547_Lv_M_WT_100-PM-061_LCM6.genes.results')
        cp.set(self.HELPER_NAME, helper_main.RSEM_GENES_RESULTS_KEY, rsem)
        ref = os.path.join(test_data_dir, 'gep_reference.txt.gz')
        cp.set(self.HELPER_NAME, helper_main.GEP_REFERENCE_KEY, ref)
        tcga = os.path.join(test_data_dir, 'tcga_data')
        cp.set(self.HELPER_NAME, helper_main.TCGA_DATA_KEY, tcga)
        # run extract step and check the results
        helper_main.extract(cp)
        gep_path = ws.abs_path('gep.txt')
        self.assertEqual(self.getMD5(gep_path), '86793b131107a466f72e64811d2b9758')
        expected = {
            'data_expression_percentile_comparison.txt': '1cbe2d84b4ff8030062b260742d1ce8e',
            'data_expression_percentile_tcga.txt': '2fe160662e3bc49d1972082d177dd610',
            'data_expression_zscores_comparison.txt': '20757c8b2126137dd05fb064734a9af4',
            'data_expression_zscores_tcga.txt': '70c92cf67705d0ad3f277a2b79d7c95a',
            'data_expression_percentile_tcga.json': '326dc17e5248416e7fa7e6b6150de79a'
        }
        for name in expected:
            out_path = os.path.join(self.tmp_dir, name)
            self.assertTrue(os.path.exists(out_path))
            self.assertEqual(self.getMD5(out_path), expected[name])

    def test_extract_unknown_tcga(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        cp = ConfigParser()
        cp.read(os.path.join(test_source_dir, 'config_unknown_tcga.ini'))
        finder = directory_finder()
        test_data_dir = os.path.join(finder.get_test_dir(), 'helpers', 'expression')
        loader = helper_loader(logging.WARNING)
        ws = workspace(self.tmp_dir)
        helper_main = loader.load(self.HELPER_NAME, ws)
        # configure the INI
        plugin_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) # go 2 directories up
        enscon = os.path.join(plugin_dir, 'ensemble_conversion_hg38.txt')
        cp.set(self.HELPER_NAME, helper_main.ENSCON_KEY, enscon)
        rsem = os.path.join(test_data_dir, 'PANX_1547_Lv_M_WT_100-PM-061_LCM6.genes.results')
        cp.set(self.HELPER_NAME, helper_main.RSEM_GENES_RESULTS_KEY, rsem)
        ref = os.path.join(test_data_dir, 'gep_reference.txt.gz')
        cp.set(self.HELPER_NAME, helper_main.GEP_REFERENCE_KEY, ref)
        tcga = os.path.join(test_data_dir, 'tcga_data')
        cp.set(self.HELPER_NAME, helper_main.TCGA_DATA_KEY, tcga)
        # run extract step and check the results
        helper_main.extract(cp)
        gep_path = ws.abs_path('gep.txt')
        self.assertEqual(self.getMD5(gep_path), '86793b131107a466f72e64811d2b9758')
        expected = {
            'data_expression_percentile_comparison.txt': '1cbe2d84b4ff8030062b260742d1ce8e',
            'data_expression_percentile_tcga.txt': 'be9c0f2588c6b75f45f8b7ab17001b84',
            'data_expression_zscores_comparison.txt': '20757c8b2126137dd05fb064734a9af4',
            'data_expression_zscores_tcga.txt': 'c841d03a6d70e0ba50be7cbac46e9a71',
            'data_expression_percentile_tcga.json': '7afda7a462ed32aea28e6eea45621fc4'
        }
        for name in expected:
            out_path = os.path.join(self.tmp_dir, name)
            self.assertTrue(os.path.exists(out_path))
            self.assertEqual(self.getMD5(out_path), expected[name])





if __name__ == '__main__':
    unittest.main()
