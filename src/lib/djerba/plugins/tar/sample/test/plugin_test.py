#! /usr/bin/env python3

"""
Test of the WGTS sample plugin
"""

import os
import string
import unittest
import tempfile
import shutil
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.tar.sample.plugin as sample
from djerba.core.workspace import workspace
from djerba.util.environment import directory_finder

class TestTarSamplePlugin(PluginTester):

    INI_NAME = 'tar.sample.ini'
    INI_NAME_NA = 'tar.sample_na.ini'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()
        #self.sample_dir = os.path.join(self.sup_dir, "plugins", "tar", "tar-sample")


    def testTarSample(self):
        # This test currently does not query GSI-QC-ETL; see GCGI-1554
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/tar/tar-sample/report_json/tar.sample.json")

        params = {
            self.INI: os.path.join(input_dir, self.INI_NAME),
            self.JSON: json_location,
            self.MD5: '2593a7d6775db7293befb5ac1f30db61'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarSampleWithNA(self):
        """
        Raw coverage and collapsed coverage are N/A and NA respectively.
        """
        test_source_dir = os.path.realpath(os.path.dirname(__file__))

        with open(os.path.join(test_source_dir, self.INI_NAME_NA)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({'DJERBA_TEST_DATA': self.sup_dir})
        input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(input_dir)
        with open(os.path.join(input_dir, self.INI_NAME_NA), 'w') as ini_file:
            ini_file.write(ini_str)
        json_location = os.path.join(self.sup_dir ,"plugins/tar/tar-sample/report_json/tar.sample_na.json")


        params = {
            self.INI: os.path.join(input_dir, self.INI_NAME_NA),
            self.JSON: json_location,
            self.MD5: 'c78eefc989cca06b1f1b67f943b85ae7'
        }
        self.run_basic_test(test_source_dir, params)


if __name__ == '__main__':
    unittest.main()
