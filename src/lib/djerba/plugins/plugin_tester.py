"""General-purpose classes to use for testing plugins"""

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
from djerba.core.main import main as core_main
from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.testing.tools import TestBase
from djerba.util.validator import path_validator

class PluginTester(TestBase):

    """
    General-purpose class for testing plugins
    - See TestDemoPlugins for usage
    - Implements *minimal* testing for a plugin; further testing is encouraged
    - Input an INI path with config for exactly one plugin
    - Check plugin runs correctly, and plugin JSON and (redacted) HTML are as expected
    - Test input/output should resemble production data as closely as possible,
      eg. data structures used in production should also appear in testing
    """

    INI = 'ini'
    JSON = 'json'
    MD5 = 'md5'
    
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

    def run_basic_test(self, test_source_dir, params, plugin_name=None):
        """
        Simple plugin test
        """
        ini_path = os.path.join(test_source_dir, params[self.INI])
        expected_json_path = os.path.join(test_source_dir, params[self.JSON])
        expected_md5 = params[self.MD5]
        if not plugin_name:
            plugin_name = self.read_plugin_name(ini_path)
        self.assertTrue(plugin_name)
        djerba_main = core_main(self.get_tmp_dir(), log_level=logging.WARNING)
        config = djerba_main.configure(ini_path)
        data_found = self.redact_json_data(djerba_main.extract(config))
        with open(expected_json_path) as json_file:
            plugin_data_expected = json.loads(json_file.read())
        plugin_data_found = data_found['plugins'][plugin_name]
        validator = plugin_json_validator(log_level=logging.WARNING)
        self.assertTrue(validator.validate_data(plugin_data_found))
        self.assertEqual(plugin_data_found, plugin_data_expected)
        html = self.redact_html(djerba_main.render(data_found))
        self.assert_report_MD5(html, expected_md5)

    # TODO add standalone tests for configure, extract, render steps
