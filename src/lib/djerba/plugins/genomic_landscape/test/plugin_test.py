#! /usr/bin/env python3

"""
Test of the genomic_landscape plugin
"""

import os
import logging
import unittest
import tempfile
import shutil
import string
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.core.workspace import workspace
from djerba.util.environment import directory_finder
from djerba.plugins.genomic_landscape.hrd import hrd_processor

class TestGenomicLandscapePlugin(PluginTester):
    
    INI_NAME = 'genomic_landscape.ini'
    BLANK = "INTENTIONALLY BLANK FOR TESTING"

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()
        self.plugin_test_dir = os.path.join(self.sup_dir, "plugins", "genomic-landscape")
        self.data_mut_ex = os.path.join(self.plugin_test_dir, "data_mutations_extended.txt")
        self.data_seg = os.path.join(self.plugin_test_dir, "data.seg")
        self.sample_info = os.path.join(self.plugin_test_dir, "sample_info.json")
        self.sample_qc = os.path.join(self.plugin_test_dir, "sample_qcs.json")
        self.sample_qc_high_cov = os.path.join(self.plugin_test_dir, "sample_qcs_high_cov.json")

    def testNCCNAnnotation(self):
        # contains oncotree file
        dir1 = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        # contains nccn annotations
        dir2 = directory_finder().get_data_dir()
        hrd = hrd_processor(log_level=logging.ERROR, log_path=None)
        self.assertEqual(hrd.annotate_NCCN("HRD", "PAAD", dir1, dir2), None)
        self.assertEqual(hrd.annotate_NCCN("HR Proficient", "HGSOC", dir1, dir2), None)
        HRD_annotated = hrd.annotate_NCCN("HRD", "HGSOC", dir1, dir2)
        self.assertEqual(HRD_annotated['Tier'], "Prognostic")

    def testGenomicLandscapeLowTmbStableMsi(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.data_mut_ex, self.tmp_dir)
        shutil.copy(self.data_seg, self.tmp_dir)
        shutil.copy(self.sample_info, self.tmp_dir)
        shutil.copy(self.sample_qc, self.tmp_dir)

        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DIR': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.plugin_test_dir, "report_json", "genomic_landscape.json")
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '690242139aab0153348e7a4634d2f17c'
        }
        self.run_basic_test(input_dir, params)

    def testGenomicLandscapeLowTmbStableMsiHighCoverage(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.data_mut_ex, self.tmp_dir)
        shutil.copy(self.data_seg, self.tmp_dir)
        shutil.copy(self.sample_info, self.tmp_dir)
        shutil.copy(self.sample_qc_high_cov, f"{self.tmp_dir}/sample_qcs.json")

        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DIR': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.plugin_test_dir, "report_json", "genomic_landscape_high_cov.json")
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '2851dc05b9e92514e1eff82f8c992663'
        }
        self.run_basic_test(input_dir, params)


    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        plot_key = 'Genomic biomarker plot'
        for key in ['HRD','TMB','MSI']:
            data['results']['genomic_biomarkers'][key][plot_key] = 'placeholder'
        return data

if __name__ == '__main__':
    unittest.main()
