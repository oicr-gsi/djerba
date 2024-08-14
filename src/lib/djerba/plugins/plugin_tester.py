"""General-purpose classes to use for testing plugins"""

import hashlib
import json
import jsonschema
import logging
import os
import re
import time
import unittest
import djerba.core.constants as core_constants

from configparser import ConfigParser
from djerba.core.json_validator import plugin_json_validator
from djerba.core.loaders import plugin_loader
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
            if section_name == core_constants.CORE:
                continue
            elif plugin_name == None:
                plugin_name = section_name
            else:
                msg = "Cannot resolve multiple plugin "+\
                      "names in {0}".format(ini_path)
                raise RuntimeError(msg)
        return plugin_name

    def run_basic_test(self, test_source_dir, params,
                       plugin_name=None, log_level=logging.WARNING, work_dir=None):
        """
        Simple plugin test
        """
        if work_dir == None:
            work_dir = self.get_tmp_dir()
        ini_path = os.path.join(test_source_dir, params[self.INI])
        expected_json_path = os.path.join(test_source_dir, params[self.JSON])
        expected_md5 = params[self.MD5]
        if not plugin_name:
            plugin_name = self.read_plugin_name(ini_path)
        self.assertTrue(plugin_name)
        # !!! First pass -- load the plugin, run as standalone, do JSON & HTML checks
        loader = plugin_loader(log_level)
        plugin = loader.load(plugin_name, workspace(work_dir, log_level))
        config = ConfigParser()
        with open(ini_path) as in_file:
            config.read_file(in_file)
        config.set(core_constants.CORE, core_constants.REPORT_ID, 'placeholder')
        plugin_config = plugin.configure(config)
        self.assertTrue(plugin_config.has_section(plugin_name))
        plugin_data_found = self.redact_json_data(plugin.extract(plugin_config))
        with open(expected_json_path) as json_file:
            plugin_data_expected = json.loads(json_file.read())
        ### uncomment this to dump the plugin output JSON to a file
        #with open('/tmp/foo.json', 'w') as out_file:
        #    out_file.write(json.dumps(plugin_data_found, sort_keys=True, indent=4))
        validator = plugin_json_validator(log_level=log_level)
        self.assertTrue(validator.validate_data(plugin_data_found))
        self.assertEqual(plugin_data_found, plugin_data_expected)
        html = plugin.render(plugin_data_found)
        ### uncomment this to dump the plugin output HTML to a file
        #with open('/tmp/foo.html', 'w') as out_file:
        #    out_file.write(html)
        self.assert_report_MD5(html, expected_md5)
        # !!! Second pass -- run the plugin as part of Djerba main, do JSON check only
        djerba_main = core_main(work_dir, log_level=log_level)
        main_config = djerba_main.configure(ini_path)
        self.assertTrue(main_config.has_section(plugin_name))
        main_data = djerba_main.extract(main_config)
        self.assertTrue(plugin_name in main_data['plugins'])
        main_plugin_data = self.redact_json_data(main_data['plugins'][plugin_name])
        self.assertEqual(main_plugin_data, plugin_data_expected)
        main_html = djerba_main.render(main_data)
        self.assertTrue(len(main_html)>0)

    # TODO add standalone tests for configure, extract, render steps
