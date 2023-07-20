#! /usr/bin/env python3

"""Test of the provenance helper"""

import logging
import os
import unittest
from configparser import ConfigParser
import djerba.core.constants as core_constants
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase


class TestProvenanceHelper(TestBase):

    CORE = 'core'
    HELPER_NAME = 'provenance_helper'
    
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
        out_path = os.path.join(self.tmp_dir, helper_main.PROVENANCE_OUTPUT)
        self.assertTrue(os.path.exists(out_path))
        self.assertEqual(self.getMD5_of_gzip_path(out_path),
                         '62c0b00c42a352d9ce3c49aedb55e8e2')
        sample_info_path = os.path.join(self.tmp_dir, core_constants.DEFAULT_SAMPLE_INFO)
        self.assertTrue(os.path.exists(sample_info_path))
        self.assertEqual(self.getMD5(sample_info_path), '406227ea4d73df43d0e4adcd02fc14cb')
        # TODO suppress console output from helper_main_2
        loader_2 = helper_loader(log_level=logging.DEBUG)
        helper_main_2 = loader_2.load(self.HELPER_NAME, ws)
        with self.assertLogs(level=logging.DEBUG) as log_context:
            helper_main_2.extract(config)
        msg = 'DEBUG:djerba.core.configure:extract: provenance_subset.tsv.gz already '+\
            'in workspace, will not overwrite'
        self.assertIn(msg, log_context.output)

if __name__ == '__main__':
    unittest.main()

