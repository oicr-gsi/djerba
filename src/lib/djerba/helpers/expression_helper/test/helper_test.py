#! /usr/bin/env python3

"""Test of the provenance helper"""

import logging
import os
import unittest
from configparser import ConfigParser
from shutil import copy
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
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
        test_dir = os.path.join(os.environ.get('DJERBA_TEST_DIR'), 'helpers', 'expression')
        sample_info = os.path.join(test_dir, 'sample_info.json')
        fpr = os.path.join(test_dir, 'provenance_subset.tsv.gz')
        copy(sample_info, work_dir)
        copy(fpr, work_dir)
        ws = workspace(work_dir)
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
        # path was derived from file provenance subset, should not change
        rsem = config.get(self.HELPER_NAME, helper_main.RSEM_GENES_RESULTS_KEY)
        self.assertEqual(self.getMD5_of_string(rsem), '46021826f0286190316af74c71d75532')
        # check the reference path
        found = config.get(self.HELPER_NAME, helper_main.GEP_REFERENCE_KEY)
        expected = os.path.join(data_dir,  'results', 'gep_reference.txt.gz')
        self.assertEqual(found, expected)

    def test_extract(self):
        test_dir = '/home/ibancarz/workspace/djerba/test/20230912_01/extract' # TODO FIXME
        cp = ConfigParser()
        cp.read(test_dir+'/config.ini')
        test_data_dir = os.path.join(
            os.environ.get(cc.DJERBA_TEST_DIR_VAR), 'helpers', 'expression'
        )
        rsem = os.path.join(test_data_dir, 'PANX_1547_Lv_M_WT_100-PM-061_LCM6.genes.results')
        cp.set(self.HELPER_NAME, 'rsem_genes_results', rsem)
        loader = helper_loader(logging.WARNING)
        ws = workspace(test_dir)
        helper_main = loader.load(self.HELPER_NAME, ws)
        helper_main.extract(cp)
        gep_path = ws.abs_path('gep.txt')
        self.assertEqual(self.getMD5(gep_path), '86793b131107a466f72e64811d2b9758')
        expected = {
            'data_expression_percentile_comparison.txt': 'da9f8c87ad8fd571b1333aa8f8228c16',
            'data_expression_percentile_tcga.txt': '6078eb231568d104505f763f997b76ca',
            'data_expression_zscores_comparison.txt': 'b2338b73e5b2ded59f30f069b7f7722a',
            'data_expression_zscores_tcga.txt': '7a040521c77f9ab1e80eaf23f417f92d'
        }
        for name in expected:
            out_path = os.path.join(test_dir, name)
            self.assertTrue(os.path.exists(out_path))
            self.assertEqual(self.getMD5(out_path), expected[name])

if __name__ == '__main__':
    unittest.main()
