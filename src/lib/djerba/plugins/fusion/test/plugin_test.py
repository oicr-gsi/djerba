#!/usr/bin/env python3

"""Test of the fusions plugin"""

import logging
import os
import string
import unittest
import tempfile
import json
from djerba.core.loaders import plugin_loader
import djerba.core.constants as constants
from shutil import copy
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.environment import directory_finder

class TestFusion(PluginTester):

    INI_NAME = 'fusion.ini'
    JSON_NAME = 'fusion.json'

    def setUp(self):
        """Set up directories and paths required for the test."""
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.data_dir_root = directory_finder().get_test_dir()
        self.data_dir = os.path.join(self.data_dir_root, constants.PLUGINS, 'fusion')
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))
        self.input_dir = os.path.join(self.get_tmp_dir(), 'input')
        os.mkdir(self.input_dir)
        self.work_dir = os.path.join(self.tmp_dir, 'work')
        os.mkdir(self.work_dir)

    def get_paths(self):
        """Return the paths needed for the test."""
        provenance_path = os.path.join(self.data_dir, 'provenance_PANX_1391.tsv.gz')
        mavis_name = 'PANX_1391_Lv_M_100-NH-020_LCM3.mavis_summary.tab'
        mavis_path = os.path.join(self.data_dir, mavis_name)
        arriba_name = 'arriba.fusions.tsv'
        arriba_path = os.path.join(self.data_dir, arriba_name)
        sample_info_path = os.path.join(self.data_dir, 'sample_info.json')
        json_path = os.path.join(self.data_dir, self.JSON_NAME)
        return provenance_path, mavis_path, arriba_path, sample_info_path, json_path

    def prepare_ini_file(self, provenance_path, mavis_path, arriba_path):
        """Prepare and return the INI file content with the correct paths."""
        with open(os.path.join(self.test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute({
            'FPR_PATH': provenance_path,
            'MAVIS_PATH': mavis_path,
            'ARRIBA_PATH': arriba_path
        })
        return ini_str

    def copy_files(self, ini_str, json_path, sample_info_path):
        """Write the INI file and copy required JSON and sample info files."""
        with open(os.path.join(self.input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(json_path, self.input_dir)
        copy(sample_info_path, self.work_dir)

    def test_process_fusion_compression(self):
        # Load the plugin
        plugin_name = self.read_plugin_name(self.INI_NAME)
        loader = plugin_loader(log_level=logging.WARNING)
        plugin = loader.load(plugin_name, workspace=self.tmp_dir)


        json_file_path = os.path.join(self.data_dir, "SND1::BRAF.json")
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")

        with open(json_file_path, "r") as json_file:
            json_data = json.load(json_file)

        # Convert JSON to string for compression
        json_string = json.dumps(json_data)

        expected_compressed_output = ("rZRtT9swEMe/ShXxYpOoE6eFtEjTxJNgEmOs1aQ9CCE3uSTeEjvELgGqfvfdXVsEfbdBVf3l+Pz/5XzxeRHcQeu0NcFBL4iF3BNSBru9wJW2m6q6qeBS1eAwmqvKAUZayKEFkwLOLQKdkbEsBiNyGVxLz+fzWpneu7PJcTkYhRR9T+FcOa++TS7Y4n3jDsJQF3f9Agw0yntoTd+2hXADoWr1aI3qnEhtHeICi1mEDm6ZxiJyRVBtMrh/Syj+NYHTB29nymSvYTOXQEcI+pSBFf7ei+KR+KrSyr0aTnLDKOHVjPMuW1tP9SNsw8sis52prMqEsyDmqUsFZPOwsFUG5kr5coWc6eKnblZ8wTThCEdw39kj7d8CHM+0f0rXOtzRlzaDlrg4JXdRYpIByZBkj2SfJCEZkYxJZMTKHskmyS7JNsk+yUbJTslWyd6YvfHqfez9TvIjWGJulU3ndPZ/UUrJgYyTJJbDKOpvRnK9A4wNo2Qk98eD/mY0DK6pXawmAA19q9I/jFsE/qHhTsHDN+dmwrhd778/jqJEjsfx3jAZRuOxxFQWT70l8fWX5/0ojm4ujj8PyDhvK4qEM1W7sGntb0h9eHU4nUYynFweTk+/hrmuINyyCly/3UH/weBmyW1bK0+ENXSzQTyahanB8Ld2dKNoU5xA40uMIiyiadt6vk0a67RfXUY0b5v1Q3CECRAg0y3mtZ48OZ0e82faFO5loSaQY3V7Z9hO7mWKeIVRkz0r3b+e5ExhsykHoUlnGl80hdtnnc0FhezZpfmUYUQ/yWtyu9VGXdcJ4glT1cLoUhT2jpodwo94GdQfdnZeFNYY6xXXAmdL0EVJm0ui5fXyLw==")
        compressed_output = plugin.compress_string(json_string)
        self.assertEqual(compressed_output, expected_compressed_output,
                         f"Compression output does not match expected result.\nExpected: {expected_compressed_output}\nGot: {compressed_output}")

    def run_fusion_test(self):
        """Execute the fusion plugin test."""
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME,
            self.MD5: '6b80957262c258a0a0641b9ab9652725'
        }
        self.run_basic_test(self.input_dir, params, 'fusion', logging.ERROR, self.work_dir)

    def test_fusion(self):
        """Complete test for fusion plugin."""
        provenance_path, mavis_path, arriba_path, sample_info_path, json_path = self.get_paths()
        ini_str = self.prepare_ini_file(provenance_path, mavis_path, arriba_path)
        self.copy_files(ini_str, json_path, sample_info_path)
        self.run_fusion_test()


if __name__ == '__main__':
    unittest.main()

