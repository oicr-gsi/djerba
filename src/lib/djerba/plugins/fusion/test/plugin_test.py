#! /usr/bin/env python3

"""Test of the fusions plugin"""

import logging
import os
import string
import unittest
import djerba.core.constants as constants
from shutil import copy
from djerba.plugins.plugin_tester import PluginTester

class TestFusion(PluginTester):

    INI_NAME = 'fusion.ini'
    JSON_NAME = 'fusion.json'

    # test uses PANX_1391 for non-empty fusion results

    def test(self):
        # customize the INI file with paths to provenance and Mavis input
        # then copy INI and JSON files to the tmp directory and run the basic test
        data_dir_root = os.getenv(constants.DJERBA_TEST_DIR_VAR)
        data_dir = os.path.join(data_dir_root, constants.PLUGINS, 'fusion')
        provenance_path = os.path.join(data_dir, 'provenance_PANX_1391.tsv.gz')
        mavis_name = 'PANX_1391_Lv_M_100-NH-020_LCM3.mavis_summary.tab'
        mavis_path = os.path.join(data_dir, mavis_name)
        json_path = os.path.join(data_dir, self.JSON_NAME)
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({
            'FPR_PATH': provenance_path,
            'MAVIS_PATH': mavis_path
        })
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(json_path, input_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME,
            self.MD5: 'b457065075945660fa0f9fbb493f5a0e'
        }
        self.run_basic_test(input_dir, params, 'fusion', logging.ERROR)

if __name__ == '__main__':
    unittest.main()

