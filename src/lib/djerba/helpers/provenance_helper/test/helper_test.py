#! /usr/bin/env python3

"""Test of the provenance helper"""

import logging
import os
import unittest
from configparser import ConfigParser
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase


class TestProvenanceHelper(TestBase):

    CORE = 'core'
    HELPER_NAME = 'provenance_helper'
    
    def test(self):
        data_dir = os.path.join(os.environ.get('DJERBA_TEST_DATA'), 'helpers', 'provenance')
        provenance_input = os.path.join(data_dir, 'provenance_input.tsv.gz')
        cp = ConfigParser()
        cp.add_section(self.CORE)
        cp.set(self.CORE, 'study_title', 'PASS01')
        cp.set(self.CORE, 'root_sample_name', 'PANX_1500')
        cp.add_section(self.HELPER_NAME)
        cp.set(self.HELPER_NAME, 'provenance_input_path', provenance_input)
        ini_path = os.path.join(self.tmp_dir, 'test.ini')
        with open(ini_path, 'w') as ini_file:
            cp.write(ini_file)
        ws = workspace(self.tmp_dir)
        loader = helper_loader(logging.WARNING)
        helper_main = loader.load(self.HELPER_NAME, ws)
        config = helper_main.configure(cp)
        helper_main.extract(config)
        out_path = os.path.join(self.tmp_dir, helper_main.PROVENANCE_OUTPUT)
        self.assertTrue(os.path.exists(out_path))
        self.assertEqual(self.getMD5_of_gzip_path(out_path),
                         '62c0b00c42a352d9ce3c49aedb55e8e2')

if __name__ == '__main__':
    unittest.main()

