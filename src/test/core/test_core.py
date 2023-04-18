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
from djerba.core.main import main, arg_processor
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
        super().setUp() # includes tmp_dir
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))


class TestArgs(TestCore):

    class mock_args:
        """Use instead of argparse to store params for testing"""

        def __init__(self, mode, work_dir, ini, ini_out, json, html, pdf):
            self.subparser_name = mode
            self.work_dir = work_dir
            self.ini = ini
            self.ini_out = ini_out
            self.json = json
            self.html = html
            self.pdf = pdf
            self.no_archive = True
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_processor(self):
        mode = 'report'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'test.ini')
        out_path = os.path.join(self.tmp_dir, 'test_out.ini')
        json = os.path.join(self.tmp_dir, 'test.json')
        html = os.path.join(self.tmp_dir, 'test.html')
        pdf = os.path.join(self.tmp_dir, 'test.pdf')
        args = self.mock_args(mode, work_dir, ini_path, out_path, json, html, pdf)
        ap = arg_processor(args)
        self.assertEqual(ap.get_mode(), mode)
        self.assertEqual(ap.get_ini_path(), ini_path)
        self.assertEqual(ap.get_ini_out_path(), out_path)
        self.assertEqual(ap.get_json_path(), json)
        self.assertEqual(ap.get_html_path(), html)
        self.assertEqual(ap.get_pdf_path(), pdf)
        self.assertEqual(ap.get_log_level(), logging.ERROR)
        self.assertEqual(ap.get_log_path(), None)

    def test_run(self):
        # run from args, with same inputs as TestSimpleReport
        # TODO add similar tests for other script modes: configure, extract, etc.
        mode = 'report'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'test.ini')
        out_path = None
        json_path = os.path.join(self.tmp_dir, 'test.json')
        html = os.path.join(self.tmp_dir, 'test.html')
        pdf = None
        args = self.mock_args(mode, work_dir, ini_path, out_path, json_path, html, pdf)
        ap = arg_processor(args)
        main(work_dir, log_level=logging.WARNING).run(args)
        json_expected = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        with open(json_expected) as json_file:
            data_expected = json.loads(json_file.read())
        with open(json_path) as json_file:
            data_found = json.loads(json_file.read())
        self.assertEqual(data_found, data_expected)
        with open(json_expected) as json_file:
            data_expected = json.loads(json_file.read())
        with open(html) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, '10f7ac3e76cc2f47f3c4f9fa4af119dd')


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
        djerba_main = main(self.tmp_dir, log_level=logging.WARNING)
        config = djerba_main.configure(ini_path)
        data_found = djerba_main.extract(config)
        with open(json_path) as json_file:
            data_expected = json.loads(json_file.read())
        self.assertEqual(data_found, data_expected)
        html = djerba_main.render(data_found)
        self.assert_report_MD5(html, '10f7ac3e76cc2f47f3c4f9fa4af119dd')

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
        ws_silent = workspace(self.tmp_dir, log_level=logging.CRITICAL)
        # test if we can write a file
        ws.write_string(self.LOREM_FILENAME, lorem)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, self.LOREM_FILENAME)))
        # test if we can read the file
        ws_lorem = ws.read_string(self.LOREM_FILENAME)
        self.assertEqual(ws_lorem, lorem)
        # test if reading a nonexistent file breaks
        with self.assertRaises(OSError):
            ws_silent.read_string('/dummy/file/path')
        # test if we can open the file
        with ws.open_file('lorem.txt') as demo_file:
            self.assertTrue(isinstance(demo_file, io.TextIOBase))
        # test if opening a nonexistent file breaks
        with self.assertRaises(OSError):
            ws_silent.open_file('/dummy/file/path')


if __name__ == '__main__':
    unittest.main()
