#! /usr/bin/env python3

import json
import logging
import os
import unittest
from configparser import ConfigParser
from copy import deepcopy
from subprocess import CalledProcessError
from time import strftime

import djerba.util.mini.constants as constants
from djerba.core.main import DjerbaVersionMismatchError
from djerba.plugins.patient_info.plugin import main as patient_info_plugin
from djerba.plugins.supplement.body.plugin import main as supplement_plugin
from djerba.util.mini.main import main
from djerba.util.testing.tools import TestBase
from djerba.util.subprocess_runner import subprocess_runner

class TestMiniBase(TestBase):

    JSON_NAME = 'simple_report_for_update.json'
    JSON_NO_SUMMARY = 'simple_report_no_summary.json'

    # TODO assert INI and summary text
    
    def assert_render(self, md5):
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        for out_path in [html_path, pdf_path]:
            self.assertTrue(os.path.isfile(out_path))
        with open(html_path) as html_file:
            original = html_file.read()
        redacted = self.redact_html(original)
        self.assertEqual(self.getMD5_of_string(redacted), md5)

    def assert_render_with_summary(self):
        self.assert_render('1493c33d6ebb0a233ca39fdcbab2bcf4')

    def assert_render_without_summary(self):
        self.assert_render('ab88d9e5bd8bf4c3f92bb480692518ca')

    def assert_setup(self, ini_path, summary_path=None):
        self.assertTrue(os.path.exists(ini_path))
        config = ConfigParser()
        config.read(ini_path)
        config.set(constants.SUPPLEMENTARY, 'report_signoff_date', 'PLACEHOLDER')
        redacted = os.path.join(self.tmp_dir, 'redacted.ini')
        with open(redacted, 'w') as out_file:
            config.write(out_file)
        self.assertEqual(self.getMD5(redacted), '258d58e8cdc60e47793790e6c0a7f9f4')
        if summary_path:
            self.assertTrue(os.path.exists(summary_path))
            self.assertEqual(self.getMD5(summary_path), 'da141119d7efe1fa8db7c98c177a90e5')


    def assert_update(self, md5):
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        json_out = os.path.join(self.tmp_dir, 'updated_report.json')
        for out_path in [html_path, pdf_path, json_out]:
            self.assertTrue(os.path.isfile(out_path))
        with open(html_path) as html_file:
            original = html_file.read()
        redacted = self.redact_html(original)
        self.assertEqual(self.getMD5_of_string(redacted), md5)
        with open(json_out) as json_file:
            json_data = json.loads(json_file.read())
        self.assertEqual(json_data['core']['extract_time'], '2023-12-20_21:38:10Z')
        dob = json_data['plugins']['patient_info']['results']['patient_dob']
        self.assertEqual(dob, '1970/01/01')
        if 'summary' in json_data['plugins']:
            text = json_data['plugins']['summary']['results']['summary_text']
            expected_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed '+\
                'do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
            self.assertEqual(text.strip(), expected_text)

    def assert_update_with_summary(self):
        self.assert_update('5683d00de0ef51aaced081b3ccd543ad')

    def assert_update_without_summary(self):
        self.assert_update('88b170c2ca4ca5e06682c67949de4154')


class TestMain(TestMiniBase):

    class mock_args_setup:
        """Use instead of argparse to store params for testing"""

        def __init__(self, out_dir, json):
            self.subparser_name = 'setup'
            self.json = json
            self.out_dir = out_dir
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    class mock_args_report:
        """Use instead of argparse to store params for testing"""

        def __init__(self, json, out_dir, pdf):
            self.subparser_name = 'render'
            self.json = json
            self.out_dir = out_dir
            self.pdf = pdf
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_setup(self):
        self.tmp_dir = '/u/ibancarz/workspace/djerba/test20240719_03'
        ini_file = os.path.join(self.tmp_dir, 'mini_djerba.ini')
        summary_file = os.path.join(self.tmp_dir, 'summary.txt')
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        args = self.mock_args_setup(self.tmp_dir, json_path)
        main(self.tmp_dir).run(args)
        self.assert_setup(ini_file, summary_file)

    def SKIPtest_setup_no_summary(self):
        out_file = os.path.join(self.tmp_dir, 'config.mdc')
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NO_SUMMARY)
        args = self.mock_args_setup(out_file, json_path)
        main(self.tmp_dir).run(args)
        self.assert_MDC_without_summary(out_file)



class TestMainOBSOLETE(TestMiniBase):
            
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

    def test_setup(self):
        out_file = os.path.join(self.tmp_dir, 'config.mdc')
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        args = self.mock_args_setup(out_file, json_path)
        main(self.tmp_dir).run(args)
        self.assert_MDC_with_summary(out_file)

    def test_setup_no_summary(self):
        out_file = os.path.join(self.tmp_dir, 'config.mdc')
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NO_SUMMARY)
        args = self.mock_args_setup(out_file, json_path)
        main(self.tmp_dir).run(args)
        self.assert_MDC_without_summary(out_file)

    def test_render(self):
        out_dir = self.tmp_dir
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, self.JSON_NAME)
        pdf = True
        args = self.mock_args_render(json_path, self.tmp_dir, pdf)
        main(self.tmp_dir).run(args)
        self.assert_render_with_summary()

    def test_render_no_summary(self):
        out_dir = self.tmp_dir
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, self.JSON_NO_SUMMARY)
        pdf = True
        args = self.mock_args_render(json_path, self.tmp_dir, pdf)
        main(self.tmp_dir).run(args)
        self.assert_render_without_summary()

    def test_version_fail(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, 'simple_report_mismatched_version.json')
        pdf = True
        write_json = True
        args = self.mock_args_update(
            config_path, json_path, self.tmp_dir, pdf, write_json, force=False
        )
        with self.assertRaises(DjerbaVersionMismatchError):
            main(self.tmp_dir, log_level=logging.CRITICAL).run(args)
        args_force = self.mock_args_update(
            config_path, json_path, self.tmp_dir, pdf, write_json, force=True
        )
        log_tmp = os.path.join(self.tmp_dir, 'test.log')
        with self.assertLogs(level=logging.WARNING) as cm:
            main(self.tmp_dir, log_path=log_tmp).run(args_force)
        self.assertTrue(cm.output[0].find('Old version = bad-version') >= 0)
        self.assertTrue(cm.output[1].find('Old version = another-bad-version') >= 0)
        self.assert_update_with_summary()

    def test_update(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, self.JSON_NAME)
        pdf = True
        write_json = True
        force = False
        args = self.mock_args_update(config_path, json_path, self.tmp_dir, pdf, write_json)
        main(self.tmp_dir).run(args)
        self.assert_update_with_summary()

    def test_update_no_summary(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, self.JSON_NO_SUMMARY)
        pdf = True
        write_json = True
        force = False
        args = self.mock_args_update(config_path, json_path, self.tmp_dir, pdf, write_json)
        main(self.tmp_dir).run(args)
        self.assert_update_without_summary()


class TestScript(TestMiniBase):

    def test_setup(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        out_path = os.path.join(self.tmp_dir, 'config.mdc')
        cmd = [
            'mini_djerba.py', 'setup',
            '--json', json_path,
            '--out', out_path
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_MDC_with_summary(out_path)

    def test_render(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        cmd = [
            'mini_djerba.py', 'render',
            '--json', json_path,
            '--out-dir', self.tmp_dir
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_render_with_summary()

    def test_render_no_pdf(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        cmd = [
            'mini_djerba.py', 'render',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--no-pdf'
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        self.assertTrue(os.path.isfile(html_path))
        self.assertFalse(os.path.isfile(pdf_path))

    def test_update(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, self.JSON_NAME)
        cmd = [
            'mini_djerba.py', 'update',
            '--config', config_path,
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--write-json'
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_update_with_summary()

    def test_update_no_pdf(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, self.JSON_NAME)
        cmd = [
            'mini_djerba.py', 'update',
            '--config', config_path,
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--write-json',
            '--no-pdf'
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        self.assertTrue(os.path.isfile(html_path))
        self.assertFalse(os.path.isfile(pdf_path))

    def test_fail(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_broken_1.mdc')
        json_path = os.path.join(test_dir, self.JSON_NAME)
        cmd = [
            'mini_djerba.py', 'update',
            '--config', config_path,
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--write-json'
        ]
        with self.assertRaises(CalledProcessError):
            subprocess_runner(log_level=logging.CRITICAL).run(cmd)
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        cmd = [
            'mini_djerba.py', 'update',
            '--config', config_path,
            '--json', '/broken/json/path',
            '--out-dir', self.tmp_dir,
            '--write-json'
        ]
        with self.assertRaises(CalledProcessError):
            subprocess_runner(log_level=logging.CRITICAL).run(cmd)



if __name__ == '__main__':
    unittest.main()

