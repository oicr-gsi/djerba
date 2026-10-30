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
        configured_tcga_enscon = config.get(self.HELPER_NAME, helper_main.TCGA_ENSCON_KEY)
        self.assertTrue(os.path.exists(configured_tcga_enscon))
        tcga_code = config.get(self.HELPER_NAME, helper_main.TCGA_CODE_KEY)
        self.assertEqual(tcga_code, 'PAAD')
        # path was derived from file provenance subset, should not change
        rsem = config.get(self.HELPER_NAME, helper_main.RSEM_GENES_RESULTS_KEY)
        self.assertEqual(self.getMD5_of_string(rsem), '6adf97f83acf6453d4a6a4b1070f3754')
        # check the reference path
        found = config.get(self.HELPER_NAME, helper_main.GEP_REFERENCE_KEY)
        expected = '/.mounts/labs/CGI/gsi/tools/djerba/gep_reference_tpm.txt.gz'
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
        enscon = os.path.join(plugin_dir, helper_main.ENSCON_DEFAULT)
        cp.set(self.HELPER_NAME, helper_main.ENSCON_KEY, enscon)
        tcga_enscon = os.path.join(plugin_dir, helper_main.TCGA_ENSCON_DEFAULT)
        cp.set(self.HELPER_NAME, helper_main.TCGA_ENSCON_KEY, tcga_enscon)
        rsem = os.path.join(test_data_dir, 'PANX_1547_Lv_M_WT_100-PM-061_LCM6.genes.results')
        cp.set(self.HELPER_NAME, helper_main.RSEM_GENES_RESULTS_KEY, rsem)
        ref = os.path.join(test_data_dir, helper_main.GEP_REFERENCE_DEFAULT)
        cp.set(self.HELPER_NAME, helper_main.GEP_REFERENCE_KEY, ref)
        tcga = os.path.join(test_data_dir, 'tcga_data')
        cp.set(self.HELPER_NAME, helper_main.TCGA_DATA_KEY, tcga)
        # run extract step and check the results
        helper_main.extract(cp)
        gep_path = ws.abs_path('gep.txt')
        self.assertEqual(self.getMD5(gep_path), '5efe8457adf3c5dd2b99116e73f80ddf')
        expected = {
            'data_expression_percentile_comparison.txt': '8de9268ea7c6fe7636cd81d3b8243fad',
            'data_expression_percentile_tcga.txt': '6fb80e9ea20272b57700ddad8bcf104f',
            'data_expression_zscores_comparison.txt': 'd75a3b56e8fde595f3ef162ac3684510',
            'data_expression_zscores_tcga.txt': 'f5a6f5e7a50090e791aa187b5b88a7d9',
            'data_expression_percentile_tcga.json': '4bf80bf81b15a84e8fd46796284d5d4d'
        }
        for name in expected:
            out_path = os.path.join(self.tmp_dir, name)
            self.assertTrue(os.path.exists(out_path))
            self.assertEqual(self.getMD5(out_path), expected[name])
        self.assertTrue(os.path.exists(ws.abs_path(helper_main.TCGA_UNMATCHED)))

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
        enscon = os.path.join(plugin_dir, helper_main.ENSCON_DEFAULT)
        cp.set(self.HELPER_NAME, helper_main.ENSCON_KEY, enscon)
        tcga_enscon = os.path.join(plugin_dir, helper_main.TCGA_ENSCON_DEFAULT)
        cp.set(self.HELPER_NAME, helper_main.TCGA_ENSCON_KEY, tcga_enscon)
        rsem = os.path.join(test_data_dir, 'PANX_1547_Lv_M_WT_100-PM-061_LCM6.genes.results')
        cp.set(self.HELPER_NAME, helper_main.RSEM_GENES_RESULTS_KEY, rsem)
        ref = os.path.join(test_data_dir, helper_main.GEP_REFERENCE_DEFAULT)
        cp.set(self.HELPER_NAME, helper_main.GEP_REFERENCE_KEY, ref)
        tcga = os.path.join(test_data_dir, 'tcga_data')
        cp.set(self.HELPER_NAME, helper_main.TCGA_DATA_KEY, tcga)
        # run extract step and check the results
        helper_main.extract(cp)
        gep_path = ws.abs_path('gep.txt')
        self.assertEqual(self.getMD5(gep_path), '5efe8457adf3c5dd2b99116e73f80ddf')
        expected = {
            'data_expression_percentile_comparison.txt': '8de9268ea7c6fe7636cd81d3b8243fad',
            'data_expression_percentile_tcga.txt': '91f8b3816168fa450e62f907714a3544',
            'data_expression_zscores_comparison.txt': 'd75a3b56e8fde595f3ef162ac3684510',
            'data_expression_zscores_tcga.txt': '2f2fd52adf57e7681e950517fe185d10',
            'data_expression_percentile_tcga.json': '5f7b238895b43f8fd9dfb5de5ac76d80'
        }
        for name in expected:
            out_path = os.path.join(self.tmp_dir, name)
            self.assertTrue(os.path.exists(out_path))
            self.assertEqual(self.getMD5(out_path), expected[name])





if __name__ == '__main__':
    unittest.main()
