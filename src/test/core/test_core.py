#! /usr/bin/env python3

import hashlib
import io
import json
import jsonschema
import logging
import os
import re
import tempfile
import time
import unittest
import djerba.util.ini_fields as ini

from configparser import ConfigParser
from djerba.core.json_validator import plugin_json_validator
from djerba.core.main import main
from djerba.core.workspace import workspace
from djerba.mergers.gene_information.merger import main as gene_information_merger_main
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.testing.tools import TestBase
from djerba.util.validator import path_validator
import djerba.util.constants as constants

class TestCore(TestBase):

    LOREM_FILENAME = 'lorem.txt'
    SIMPLE_REPORT_JSON = 'simple_report_expected.json'

    def setUp(self):
        super().setUp()
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()
    
class TestMerger(TestCore):

    GENE_INFO_INPUTS = 'gene_information_inputs.json'

    def test_gene_info(self):
        json_path = os.path.join(self.test_source_dir, self.GENE_INFO_INPUTS)
        with open(json_path) as json_file:
            inputs = json.loads(json_file.read())
        html = gene_information_merger_main().render(inputs)
        md5_found = self.getMD5_of_string(html)
        self.assertEqual(md5_found, 'd436df8d05a8af3cbdf71a15eb12f7ea')

class TestSimpleReport(TestCore):

    def test_report(self):
        ini_path = os.path.join(self.test_source_dir, 'test.ini')
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        djerba_main = main(log_level=logging.WARNING)
        config = djerba_main.configure(ini_path)
        data_found = djerba_main.extract(config)
        with open(json_path) as json_file:
            data_expected = json.loads(json_file.read())
        self.assertEqual(data_found, data_expected)
        html = djerba_main.render(data_found)
        self.assert_report_MD5(html, '094f5e6f896f9c9eaa740223530298ba')

class TestValidator(TestCore):

    EXAMPLE_DEFAULT = 'plugin_example.json'
    EXAMPLE_EMPTY = 'plugin_example_empty.json'
    EXAMPLE_BROKEN = 'plugin_example_broken.json'

    def run_script(self, in_path):
        runner = subprocess_runner(log_level=logging.CRITICAL)
        with open(in_path) as in_file:
            input_string = in_file.read()
        result = runner.run(['validate_plugin_json.py'], stdin=input_string, raise_err=False)
        return result.returncode

    def test_plugin(self):
        validator = plugin_json_validator(log_level=logging.WARNING)
        for filename in [self.EXAMPLE_DEFAULT, self.EXAMPLE_EMPTY]:
            in_path = os.path.join(self.test_source_dir, filename)
            with open(in_path) as in_file:
                input_data = json.loads(in_file.read())
            self.assertTrue(validator.validate_data(input_data))

    def test_plugin_broken(self):
        validator = plugin_json_validator(log_level=logging.CRITICAL)
        in_path = os.path.join(self.test_source_dir, self.EXAMPLE_BROKEN)
        with open(in_path) as in_file:
            input_data = json.loads(in_file.read())
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validator.validate_data(input_data)

    def test_script(self):
        good_path = os.path.join(self.test_source_dir, self.EXAMPLE_DEFAULT)
        self.assertEqual(self.run_script(good_path), 0)
        # complete report JSON doesn't (and shouldn't) satisfy the plugin schema
        bad_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        self.assertEqual(self.run_script(bad_path), 3)

class TestWorkspace(TestCore):

    def test(self):
        with open(os.path.join(self.test_source_dir, self.LOREM_FILENAME)) as in_file:
            lorem = in_file.read()
        ws = workspace(self.tmp_dir)
        # test if we can write a file
        ws.write_string(self.LOREM_FILENAME, lorem)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, self.LOREM_FILENAME)))
        # test if we can read the file
        ws_lorem = ws.read_string(self.LOREM_FILENAME)
        self.assertEqual(ws_lorem, lorem)
        # test if we can open the file
        with ws.open_file('lorem.txt') as demo_file:
            self.assertTrue(isinstance(demo_file, io.TextIOBase))

if __name__ == '__main__':
    unittest.main()
