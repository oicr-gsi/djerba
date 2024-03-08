#! /usr/bin/env python3

"""Test of the VAF helper"""

import logging
import os
import unittest
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase
from djerba.util.environment import directory_finder

class TestVafHelper(TestBase):

    HELPER_NAME = 'vaf_helper'

    def test(self):
        self.data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(self.data_dir_root, 'helpers', self.HELPER_NAME)
        maf_name = 'PANX_1391_Lv_M_WG_100-NH-020_LCM3.filter.deduped.realigned.'+\
            'recalibrated.mutect2.filtered.subset.maf.gz'
        maf_path = os.path.join(data_dir, maf_name)
        ws = workspace(self.tmp_dir)
        loader = helper_loader(logging.WARNING)
        helper_main = loader.load(self.HELPER_NAME, ws)
        config = helper_main.get_expected_config()
        config.add_section('core')
        config.set(self.HELPER_NAME, 'maf_path', maf_path)
        config = helper_main.configure(config)
        helper_main.extract(config)
        output_path = os.path.join(self.tmp_dir, 'vaf_by_gene.json')
        self.assertTrue(os.path.exists(output_path))


if __name__ == '__main__':
    unittest.main() 

