#! /usr/bin/env python3

"""Test of the provenance helper"""

import logging
import os
import unittest
from configparser import ConfigParser
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase


class TestExpressionHelper(TestBase):

    CORE = 'core'
    HELPER_NAME = 'expression_helper'
    
    def test_configure(self):
        cp = ConfigParser()
        cp.add_section(self.CORE)
        cp.set(self.CORE, 'project', 'PASS01')
        cp.set(self.CORE, 'donor', 'PANX_1500')
        cp.add_section(self.HELPER_NAME)        
        loader = helper_loader(logging.WARNING)
        test_dir = '/home/ibancarz/workspace/djerba/test/20230808_03/configure' # TODO FIXME
        ws = workspace(test_dir)
        helper_main = loader.load(self.HELPER_NAME, ws)
        config = helper_main.configure(cp)
        data_dir = os.environ.get('DJERBA_DATA_DIR')
        if not data_dir:
            raise RuntimeError('DJERBA_DATA_DIR environment variable is not configured')
        expected_enscon = os.path.join(data_dir, 'ensemble_conversion_hg38.txt')
        configured_enscon = config.get(self.HELPER_NAME, helper_main.ENSCON_KEY)
        self.assertEqual(configured_enscon, expected_enscon)
        expected_gene_list = os.path.join(data_dir, 'targeted_genelist.txt')
        configured_gene_list = config.get(self.HELPER_NAME, helper_main.GENE_LIST_KEY)
        self.assertEqual(configured_gene_list, expected_gene_list)
        tcga_code = config.get(self.HELPER_NAME, helper_main.TCGA_CODE_KEY)
        self.assertEqual(tcga_code, 'PAAD')
        rsem_path = config.get(self.HELPER_NAME, helper_main.RSEM_GENES_RESULTS_KEY)
        self.assertEqual(self.getMD5_of_string(rsem_path), 'b676a42e2637f6cef80929bc0f4367f8')

    def test_extract(self):
        test_dir = '/home/ibancarz/workspace/djerba/test/20230808_03/extract' # TODO FIXME
        cp = ConfigParser()
        cp.read(test_dir+'/configured.ini')
        loader = helper_loader(logging.DEBUG)
        ws = workspace(test_dir)
        helper_main = loader.load(self.HELPER_NAME, ws)
        helper_main.extract(cp)
        gep_path = ws.abs_path('gep.txt')
        self.assertEqual(self.getMD5(gep_path), '56e3a38493f1dcb76e0d10343b92130c')
        expected = {
            'data_expression_percentile_comparison.txt': 'abe21376344160a8c4101f772bc484b9',
            'data_expression_percentile_tcga.txt': '06fcbe6e2ef2be26e2f044c8fcb9948b',
            'data_expression_zscores_comparison.txt': '5be91225fea2b7ed1fbdb59459d61346',
            'data_expression_zscores_tcga.txt': '3f0fead97a729fd88fb7fdd69f2e305c'
        }
        for name in expected:
            out_path = os.path.join(test_dir, name)
            self.assertTrue(os.path.exists(out_path))
            self.assertEqual(self.getMD5(out_path), expected[name])

if __name__ == '__main__':
    unittest.main()
