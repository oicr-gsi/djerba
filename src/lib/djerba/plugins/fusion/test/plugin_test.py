#! /usr/bin/env python3

"""Test of the fusions plugin"""

import logging
import os
import string
import unittest
import djerba.core.constants as constants
from shutil import copy
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.environment import directory_finder

class TestFusion(PluginTester):

    INI_NAME = 'fusion.ini'
    JSON_NAME = 'fusion.json'

    # test uses PANX_1391 for non-empty fusion results

    def test(self):
        # customize the INI file with paths to provenance and Mavis input
        # then copy INI and JSON files to the tmp directory and run the basic test
        data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(data_dir_root, constants.PLUGINS, 'fusion')
        provenance_path = os.path.join(data_dir, 'provenance_PANX_1391.tsv.gz')
        mavis_name = 'PANX_1391_Lv_M_100-NH-020_LCM3.mavis_summary.tab'
        mavis_path = os.path.join(data_dir, mavis_name)
        sample_info_path = os.path.join(data_dir, 'sample_info.json')
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
        work_dir = os.path.join(self.tmp_dir, 'work')
        os.mkdir(work_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(json_path, input_dir)
        copy(sample_info_path, work_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME,
            self.MD5: '2d038fbe4014283df7c34228a58f3be0'
        }
        self.run_basic_test(input_dir, params, 'fusion', logging.ERROR, work_dir)

if __name__ == '__main__':
    unittest.main()

