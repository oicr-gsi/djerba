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
        self.data_mut_ex = os.path.join(self.sup_dir, "plugins/genomic-landscape/data_mutations_extended.txt")
        self.data_seg = os.path.join(self.sup_dir, "plugins/genomic-landscape/data.seg")
        self.sample_info = os.path.join(self.sup_dir, "plugins/genomic-landscape/sample_info.json")

    def testNCCNAnnotation(self):
        data_dir = directory_finder().get_data_dir()
        hrd = hrd_processor(log_level=logging.ERROR, log_path=None)
        self.assertEqual(hrd.annotate_NCCN("HRD", "PAAD", data_dir), None)
        self.assertEqual(hrd.annotate_NCCN("HR Proficient", "HGSOC", data_dir), None)
        HRD_annotated = hrd.annotate_NCCN("HRD", "HGSOC", data_dir)
        self.assertEqual(HRD_annotated['Tier'], "Prognostic")

    def testGenomicLandscapeLowTmbStableMsi(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        # Copy files into the temporary directory
        shutil.copy(self.data_mut_ex, self.tmp_dir)
        shutil.copy(self.data_seg, self.tmp_dir)
        shutil.copy(self.sample_info, self.tmp_dir)

        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DIR': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/genomic-landscape/report_json/genomic_landscape.json")

        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_location,
            self.MD5: '9ce53bdd5883af1d8b515187b7aa7e98'
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
