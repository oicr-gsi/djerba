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
from djerba.util.environment import directory_finder

class TestProvenance(TestBase):

    HELPER_NAME = 'pwgs_provenance_helper'
    CORE = 'core'
    SUBSET_MD5 = 'd41d8cd98f00b204e9800998ecf8427e'
    PATH_INFO_MD5 = '78330d60b6c5411f16e2a04f09a01e87'

    def testGetProvenance(self):
        self.data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(self.data_dir_root, 'helpers', 'provenance')
        provenance_input = os.path.join(data_dir, 'provenance_input.tsv.gz')
        ws = workspace(self.tmp_dir)
        loader = helper_loader(logging.WARNING)
        helper_main = loader.load(self.HELPER_NAME, ws)
        config = helper_main.get_expected_config()
        config.add_section(self.CORE)
        config.set(self.HELPER_NAME, 'project', 'PWGVAL')
        config.set(self.HELPER_NAME, 'requisition_id', 'PWGVAL_011418_Ct')
        config.set(self.HELPER_NAME, 'provenance_input_path', provenance_input)
        config = helper_main.configure(config)
        subset_path = os.path.join(self.tmp_dir, helper_main.PROVENANCE_OUTPUT)
        self.assertTrue(os.path.exists(subset_path))
        self.assertEqual(self.getMD5_of_gzip_path(subset_path), self.SUBSET_MD5)
        path_info_path = os.path.join(self.tmp_dir, core_constants.DEFAULT_PATH_INFO)
        self.assertTrue(os.path.exists(path_info_path))
        self.assertEqual(self.getMD5(path_info_path), self.PATH_INFO_MD5)

if __name__ == '__main__':
    unittest.main() 