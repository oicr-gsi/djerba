#! /usr/bin/env python3

"""Test of the provenance helper"""

import logging
import os
import time
import unittest
from configparser import ConfigParser
import djerba.core.constants as core_constants
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase
import djerba.helpers.pwgs_provenance_helper.helper as pwgs_helper

class TestCardea(TestBase):

    HELPER_NAME = 'pwgs_provenance_helper'
    CORE = 'core'
    SUBSET_MD5 = '36436b2f7894e774e23f6b68a4f73972'
    SAMPLE_INFO_MD5 = 'eefba097b9449123a66da62beb22c709'
    PATH_INFO_MD5 = '78330d60b6c5411f16e2a04f09a01e87'

    def testGetCardea(self):
        CARDEA_URL='https://cardea.gsi.oicr.on.ca/requisition-cases'
        requisition_id = "PWGVAL_011418_Ct"
        requisition_info = pwgs_helper.main.get_cardea(self, requisition_id, CARDEA_URL)
        self.assertEqual(requisition_info["assay_name"], 'pWGS - 30X')
        self.assertEqual(requisition_info["project"], 'PWGVAL')
        self.assertEqual(requisition_info["provenance_id"], 'OCT_011418_Ct_T_nn_1-11_LB01-01')

    def testGetProvenance(self):
        data_dir = os.path.join(os.environ.get('DJERBA_TEST_DATA'), 'helpers', 'provenance')
        provenance_input = os.path.join(data_dir, 'provenance_input.tsv.gz')
        ws = workspace(self.tmp_dir)
        loader = helper_loader(logging.WARNING)
        helper_main = loader.load(self.HELPER_NAME, ws)
        config = helper_main.get_expected_config()
        config.add_section(self.CORE)
        config.set(self.HELPER_NAME, 'requisition_id', 'PWGVAL_011418_Ct')
        config.set(self.HELPER_NAME, 'provenance_input_path', provenance_input)
        config = helper_main.configure(config)
        subset_path = os.path.join(self.tmp_dir, helper_main.PROVENANCE_OUTPUT)
        self.assertTrue(os.path.exists(subset_path))
        self.assertEqual(self.getMD5_of_gzip_path(subset_path), self.SUBSET_MD5)
        sample_info_path = os.path.join(self.tmp_dir, core_constants.DEFAULT_SAMPLE_INFO)
        self.assertTrue(os.path.exists(sample_info_path))
        self.assertEqual(self.getMD5(sample_info_path), self.SAMPLE_INFO_MD5)
        path_info_path = os.path.join(self.tmp_dir, core_constants.DEFAULT_PATH_INFO)
        self.assertTrue(os.path.exists(path_info_path))
        self.assertEqual(self.getMD5(path_info_path), self.PATH_INFO_MD5)

if __name__ == '__main__':
    unittest.main() 