#! /usr/bin/env python3

import hashlib
import json
import jsonschema
import logging
import os
import re
import time
import unittest
import djerba.util.ini_fields as ini

from configparser import ConfigParser
from djerba.core.json_validator import plugin_json_validator
from djerba.core.main import main
from djerba.util.validator import path_validator
import djerba.util.constants as constants

class TestBase(unittest.TestCase):

    def setUp(self):
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))
        self.maxDiff = None

    def assert_report_MD5(self, report_string, expected_md5):
        # based on check_report() from original djerba test.py
        # substitute out any date strings and check md5sum of the report body
        contents = re.split("\n", report_string)
        # crudely parse out the HTML body, omitting <img> tags
        # could use an XML parser instead, but this way is simpler
        body_lines = []
        in_body = False
        for line in contents:
            if re.search('<body>', line):
                in_body = True
            elif re.search('</body>', line):
                break
            elif in_body and not re.search('<img src=', line):
                body_lines.append(line)
        body = ''.join(body_lines)
        body = body.replace(time.strftime("%Y/%m/%d"), '0000/00/31')
        self.assertEqual(self.getMD5_of_string(body), expected_md5)
    
    def getMD5(self, inputPath):
        with open(inputPath, 'rb') as f:
            md5sum = self.getMD5_of_string(f.read())
        return md5sum

    def getMD5_of_string(self, input_string):
        md5 = hashlib.md5()
        md5.update(input_string.encode(constants.TEXT_ENCODING))
        return md5.hexdigest()

    
class TestPwgsPlugins(TestBase):

    def test_pwgs_analysis(self):
        ini_path = os.path.join(self.test_source_dir, 'data/pwgs.analysis.ini')
        json_path = os.path.join(self.test_source_dir, 'data/report/pwgs.analysis.json')
        expected_md5 = 'c9f0826bd58cab5c38b1e5fba98fb1eb'
        PluginTester().run(ini_path, json_path, expected_md5)

class PluginTester(TestBase):

    """
    General-purpose class for testing plugins
    - See TestDemoPlugins for usage
    - Implements *minimal* testing for a plugin; further testing is encouraged
    - Input an INI path with config for exactly one plugin
    - Check plugin runs correctly, and plugin JSON and (redacted) HTML are as expected
    - Test input/output should resemble production data as closely as possible,
      eg. data strucutres used in production should also appear in testing
    """

    def read_plugin_name(self, ini_path):
        """Check for exactly one plugin name in config; raise an error if unsuccessful"""
        path_validator().validate_input_file(ini_path)
        config = ConfigParser()
        config.read(ini_path)
        plugin_name = None
        for section_name in config.sections():
            if section_name == ini.CORE:
                continue
            elif plugin_name == None:
                plugin_name = section_name
            else:
                msg = "Cannot resolve multiple plugin "+\
                      "names in {0}".format(ini_path)
                raise RuntimeError(msg)
        return plugin_name

    def run(self, ini_path, expected_json_path, report_md5):
        self.maxDiff = None
        plugin_name = self.read_plugin_name(ini_path)
        self.assertTrue(plugin_name)
        djerba_main = main(log_level=logging.WARNING)
        config = djerba_main.configure(ini_path)
        data_found = djerba_main.extract(config)
        with open(expected_json_path) as json_file:
            plugin_data_expected = json.loads(json_file.read())
        plugin_data_found = data_found['plugins'][plugin_name]
        validator = plugin_json_validator(log_level=logging.WARNING)
        self.assertTrue(validator.validate_data(plugin_data_found))
        self.assertEqual(plugin_data_found, plugin_data_expected)
        html = djerba_main.render(data_found)
        self.assert_report_MD5(html, report_md5)      

if __name__ == '__main__':
    unittest.main()
