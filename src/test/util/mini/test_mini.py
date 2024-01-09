#! /usr/bin/env python3

import json
import logging
import os
import unittest

from djerba.plugins.patient_info.plugin import main as patient_info_plugin
from djerba.util.mini.main import main
from djerba.util.mini.mdc import mdc, MDCFormatError
from djerba.util.testing.tools import TestBase
from djerba.util.subprocess_runner import subprocess_runner

class TestMDC(TestBase):

    def test_read(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        test_file = os.path.join(test_dir, 'config.mdc')
        patient_info, text = mdc().read(test_file)
        self.assertEqual(patient_info, patient_info_plugin.PATIENT_DEFAULTS)
        self.assertEqual(text, 'Hello, world!')

    def test_read_fail(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        test_files = [
            'config_broken_1.mdc',
            'config_broken_2.mdc',
            'config_broken_3.mdc',
            'config_broken_4.mdc',
            'config_broken_5.mdc'
        ]
        for file_name in test_files:
            with self.assertRaises(MDCFormatError):
                mdc(log_level=logging.CRITICAL).read(os.path.join(test_dir, file_name))

    def test_write(self):
        out_path = os.path.join(self.tmp_dir, 'config.mdc')
        patient_info = patient_info_plugin.PATIENT_DEFAULTS
        patient_info['patient_name'] = 'Smith, John'
        patient_info['physician_name'] = 'Doe, Jane'
        text = 'Lorem ipsum dolor sit amet'
        mdc().write(out_path, patient_info, text)
        self.assertTrue(os.path.isfile(out_path))
        patient_info_new, text_new = mdc().read(out_path)
        self.assertEqual(patient_info, patient_info_new)
        self.assertEqual(patient_info_new['patient_name'], 'Smith, John')
        self.assertEqual(text, text_new)

class TestMiniBase(TestBase):

    JSON_NAME = 'simple_report_for_update.json'

    def assert_MDC(self, out_path):
        self.assertTrue(os.path.isfile(out_path))
        self.assertEqual(self.getMD5(out_path), '48efe0ce5121a1878ebfc04f143f49cc')

    def assert_update(self):
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        json_out = os.path.join(self.tmp_dir, 'updated_report.json')
        for out_path in [html_path, pdf_path, json_out]:
            self.assertTrue(os.path.isfile(out_path))
        with open(html_path) as html_file:
            redacted = self.redact_html(html_file.read())
        self.assertEqual(self.getMD5_of_string(redacted), 'bf06a4b1959df709ca95720dc2841110')
        with open(json_out) as json_file:
            json_data = json.loads(json_file.read())
        dob = json_data['plugins']['patient_info']['results']['patient_dob']
        self.assertEqual(dob, '1970/01/01')
        text = json_data['plugins']['summary']['results']['summary_text']
        expected_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed '+\
            'do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        self.assertEqual(text, expected_text)


class TestMain(TestMiniBase):

    class mock_args_ready:
        """Use instead of argparse to store params for testing"""

        def __init__(self, out_file, json):
            self.subparser_name = 'ready'
            self.json = json
            self.out = out_file
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    class mock_args_update:
        """Use instead of argparse to store params for testing"""

        def __init__(self, config_path, json, out_dir, pdf, write_json, force=False):
            self.subparser_name = 'update'
            self.config = config_path
            self.json = json
            self.out_dir = out_dir
            self.pdf = pdf
            self.write_json = write_json
            self.force = force
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_ready(self):
        out_file = os.path.join(self.tmp_dir, 'config.mdc')
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        args = self.mock_args_ready(out_file, json_path)
        main(self.tmp_dir).run(args)
        self.assert_MDC(out_file)

    def test_update(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, self.JSON_NAME)
        pdf = True
        write_json = True
        force = False
        args = self.mock_args_update(config_path, json_path, self.tmp_dir, pdf, write_json)
        main(self.tmp_dir).run(args)
        self.assert_update()

    class TestScript(TestMiniBase):

        def test_ready(self):
            test_dir = os.path.dirname(os.path.realpath(__file__))
            json_path = os.path.join(test_dir, self.JSON_NAME)
            out_path = os.path.join(self.tmp_dir, 'config.mdc')
            cmd = [
                'mini_djerba.py', 'ready',
                '--json', json_path,
                '--out', out_path
            ]
            result = subprocess_runner().run(cmd)
            self.assertEqual(result.returncode, 0)
            self.assertMDC(out_path)

        def test_update(self):
            test_dir = os.path.dirname(os.path.realpath(__file__))
            config_path = os.path.join(test_dir, 'config_for_update.mdc')
            json_path = os.path.join(test_dir, self.JSON_NAME)
            cmd = [
                'mini_djerba.py', 'update',
                '--config', config_path,
                '--json', json_path,
                '--out_dir', self.tmp_dir,
                '--pdf',
                '--write-json'
            ]
            result = subprocess_runner().run(cmd)
            self.assertEqual(result.returncode, 0)
            self.assert_update()


if __name__ == '__main__':
    unittest.main()

