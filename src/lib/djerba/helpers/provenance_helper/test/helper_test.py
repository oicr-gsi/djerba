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


class TestProvenanceHelper(TestBase):

    CORE = 'core'
    HELPER_NAME = 'provenance_helper'
    SUBSET_MD5 = '62c0b00c42a352d9ce3c49aedb55e8e2'
    INFO_MD5 = '5d358d76c0013748b5fc34c52b6abe56'
    
    def test(self):
        data_dir = os.path.join(os.environ.get('DJERBA_TEST_DATA'), 'helpers', 'provenance')
        provenance_input = os.path.join(data_dir, 'provenance_input.tsv.gz')
        ws = workspace(self.tmp_dir)
        loader = helper_loader(logging.WARNING)
        helper_main = loader.load(self.HELPER_NAME, ws)
        config = helper_main.get_expected_config()
        config.add_section(self.CORE)
        config.set(self.HELPER_NAME, 'study_title', 'PASS01')
        config.set(self.HELPER_NAME, 'root_sample_name', 'PANX_1500')
        config.set(self.HELPER_NAME, 'provenance_input_path', provenance_input)
        config = helper_main.configure(config)
        subset_path = os.path.join(self.tmp_dir, helper_main.PROVENANCE_OUTPUT)
        self.assertTrue(os.path.exists(subset_path))
        self.assertEqual(self.getMD5_of_gzip_path(subset_path), self.SUBSET_MD5)
        sample_info_path = os.path.join(self.tmp_dir, core_constants.DEFAULT_SAMPLE_INFO)
        self.assertTrue(os.path.exists(sample_info_path))
        self.assertEqual(self.getMD5(sample_info_path), self.INFO_MD5)
        subset_mod = os.path.getmtime(subset_path)
        info_mod = os.path.getmtime(sample_info_path)
        time.sleep(0.01) # delay to enable file modification time check
        helper_main.extract(config) # should do nothing
        self.assertEqual(os.path.getmtime(subset_path), subset_mod)
        self.assertEqual(os.path.getmtime(sample_info_path), info_mod)
        ws.remove_file(subset_path)
        ws.remove_file(sample_info_path)
        helper_main.extract(config) # should regenerate the files
        self.assertTrue(os.path.exists(subset_path))
        self.assertEqual(self.getMD5_of_gzip_path(subset_path), self.SUBSET_MD5)
        sample_info_path = os.path.join(self.tmp_dir, core_constants.DEFAULT_SAMPLE_INFO)
        self.assertTrue(os.path.exists(sample_info_path))
        self.assertEqual(self.getMD5(sample_info_path), self.INFO_MD5)


if __name__ == '__main__':
    unittest.main()

