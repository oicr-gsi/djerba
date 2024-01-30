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
    SUBSET_MD5 = '41c9288d5159f960f0193939a411a113'
    SAMPLE_INFO_MD5 = '6eaf49a1c0e558b6861c328b963e9497'
    PATH_INFO_MD5 = '213db825db81cbdc75a8a36c2508489e'
    
    def test(self):
        data_dir = os.path.join(os.environ.get('DJERBA_TEST_DIR'), 'helpers', 'provenance')
        provenance_input = os.path.join(data_dir, 'provenance_input.tsv.gz')
        ws = workspace(self.tmp_dir)
        loader = helper_loader(logging.WARNING)
        helper_main = loader.load(self.HELPER_NAME, ws)
        config = helper_main.get_expected_config()
        config.add_section(self.CORE)
        config.set(self.HELPER_NAME, 'project', 'PASS01')
        config.set(self.HELPER_NAME, 'donor', 'PANX_1500')
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
        subset_mod = os.path.getmtime(subset_path)
        sample_info_mod = os.path.getmtime(sample_info_path)
        path_info_mod = os.path.getmtime(sample_info_path)
        time.sleep(0.01) # delay to enable file modification time check
        helper_main.extract(config) # should do nothing
        self.assertTrue(abs(os.path.getmtime(subset_path) - subset_mod)<0.0001)
        self.assertTrue(abs(os.path.getmtime(sample_info_path) - sample_info_mod)<0.0001)
        self.assertTrue(abs(os.path.getmtime(path_info_path) - path_info_mod)<0.0001)
        ws.remove_file(subset_path)
        ws.remove_file(sample_info_path)
        ws.remove_file(path_info_path)
        helper_main.extract(config) # should regenerate the files
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
