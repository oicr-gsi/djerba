#! /usr/bin/env python3

"""
Test of the snv tools
"""

import os
import unittest
import tempfile

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.snv_indel_tools.preprocess import preprocess
from djerba.snv_indel_tools.extract import data_builder as data_extractor
from djerba.snv_indel_tools.preprocess import preprocess

class TestTarSamplePlugin(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

    def test_get_cytoband(self):
        gene = "AADAC"
        cytoband = data_extractor("TAR","PAAD").get_cytoband(gene)
        self.assertEqual(cytoband, "3q25.1")

    def test_build_small_mutations_and_indels(self):
        data_extended_oncogenic = os.path.join(self.sup_dir ,"report_example/data_mutations_extended_oncogenic.txt")
        small_mutations_data = data_extractor( "TAR","PAAD").build_small_mutations_and_indels(data_extended_oncogenic)
        self.assertEqual(small_mutations_data, [{'Gene': 'KRAS', 'Gene_URL': 'https://www.oncokb.org/gene/KRAS', 'Chromosome': '12p12.1', 'Protein': 'p.G12S', 'Protein_URL': 'https://www.oncokb.org/gene/KRAS/p.G12S/PAAD', 'Type': 'Missense Mutation', 'Expression Percentile': None, 'VAP (%)': 46, 't_depth': 211, 't_alt_count': 98, 'OncoKB': 'Level 4'}, {'Gene': 'TP53', 'Gene_URL': 'https://www.oncokb.org/gene/TP53', 'Chromosome': '17p13.1', 'Protein': 'p.R273H', 'Protein_URL': 'https://www.oncokb.org/gene/TP53/p.R273H/PAAD', 'Type': 'Missense Mutation', 'Expression Percentile': None, 'VAP (%)': 55, 't_depth': 127, 't_alt_count': 70, 'OncoKB': 'Oncogenic'}])
        pass

    #def test_read_maf_indices(self):
    #    maf_file = os.path.join(self.sup_dir ,"GSICAPBENCH_1219_Lv_M_WG_100-009-005_LCM3.filter.deduped.realigned.recalibrated.mutect2.filtered.reduced.maf.gz")

    # def test_preprocess_maf(self):
    #     #read raw maf, process and count rows 
    #     maf_file = os.path.join(self.sup_dir ,"GSICAPBENCH_1219_Lv_M_WG_100-009-005_LCM3.filter.deduped.realigned.recalibrated.mutect2.filtered.reduced.maf.gz")
    #     tmp_file = preprocess('config', self.tmp_dir, 'assay', 'identifier').preprocess_maf( maf_file, "WGTS", "100-PM-013_LCM5")
    #     with open(tmp_file, 'r') as fp:
    #         for count, line in enumerate(fp):
    #             pass
    #     self.assertEqual(count, 100)

if __name__ == '__main__':
    unittest.main()
