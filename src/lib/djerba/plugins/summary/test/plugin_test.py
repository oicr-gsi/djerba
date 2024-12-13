#! /usr/bin/env python3

"""Test of the summary plugin"""

import os
import unittest
import tempfile
from configparser import ConfigParser

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.environment import directory_finder

class TestSummaryPlugin(PluginTester):
    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.data_dir_root = directory_finder().get_test_dir()

    def testSummary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.data_dir_root, "plugins", "summary", "report_json", "summary.json")
        params = {
            self.INI: 'summary.ini',
            self.JSON: json_location,
            self.MD5: '155e22cc02a45e04dc9058112354367c'
        }
        self.run_basic_test(test_source_dir, params)

    def testSummaryWithCustomText(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        summary_path = os.path.join(test_source_dir, 'custom_summary.txt')
        config = ConfigParser()
        config.add_section('core')
        config.add_section('summary')
        config.set('summary', 'summary_file', summary_path)
        ini_path = os.path.join(self.tmp_dir, 'custom_summary.ini')
        with open(ini_path, 'w') as ini_file:
            config.write(ini_file)
        json_location = os.path.join(self.data_dir_root, "plugins", "summary", "report_json", "custom_summary.json")
        params = {
            self.INI: ini_path,
            self.JSON: json_location,
            self.MD5: 'cebbb53b9b074131e309dca71704a896'
        }
        self.run_basic_test(test_source_dir, params)


if __name__ == '__main__':
    unittest.main()
