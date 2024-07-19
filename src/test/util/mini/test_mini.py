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
    REPORT_MD5 = 'ec3d64a84e2c288c894c7826af5faffa'
    REPORT_NO_SUMMARY_MD5 = '9f2f74e9695f371d58774fd454755d0e'

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
        else:
            summary_path = os.path.join(self.tmp_dir, 'summary.txt')
            self.assertFalse(os.path.exists(summary_path))

    def assert_report(self, md5, pdf=True):
        html_path = os.path.join(self.tmp_dir, 'PLACEHOLDER_report.clinical.html')
        self.assertTrue(os.path.exists(html_path))
        with open(html_path) as in_file:
            html = in_file.read()
        redacted = self.redact_html(html)
        self.assertEqual(self.getMD5_of_string(redacted), md5)
        if pdf:
            pdf_path = os.path.join(self.tmp_dir, 'PLACEHOLDER_report.clinical.pdf')
            self.assertTrue(os.path.exists(html_path))


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

        def __init__(self, json, ini_path, summary_path, out_dir):
            self.subparser_name = 'report'
            self.json = json
            self.out_dir = out_dir
            self.pdf = True
            self.force = False
            self.summary = summary_path
            self.ini = ini_path
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_report(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        ini_path = os.path.join(test_dir, 'mini_djerba.ini')
        summary_path = os.path.join(test_dir, 'lorem.txt')
        args = self.mock_args_report(json_path, ini_path, summary_path, self.tmp_dir)
        main(self.tmp_dir).run(args)
        self.assert_report(self.REPORT_MD5)

    def test_setup(self):
        ini_file = os.path.join(self.tmp_dir, 'mini_djerba.ini')
        summary_file = os.path.join(self.tmp_dir, 'summary.txt')
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        args = self.mock_args_setup(self.tmp_dir, json_path)
        main(self.tmp_dir).run(args)
        self.assert_setup(ini_file, summary_file)

    def test_setup_no_summary(self):
        ini_file = os.path.join(self.tmp_dir, 'mini_djerba.ini')
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NO_SUMMARY)
        args = self.mock_args_setup(self.tmp_dir, json_path)
        main(self.tmp_dir).run(args)
        self.assert_setup(ini_file)


class TestScript(TestMiniBase):

    def test_report(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        ini_path = os.path.join(test_dir, 'mini_djerba.ini')
        summary_path = os.path.join(test_dir, 'lorem.txt')
        cmd = [
            'mini_djerba.py', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--ini', ini_path,
            '--summary', summary_path
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_report(self.REPORT_MD5)

    def test_report_fail(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        summary_path = os.path.join(test_dir, 'lorem.txt')
        cmd = [
            'mini_djerba.py', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--ini', os.path.join(test_dir, 'mini_djerba_broken.ini'),
            '--summary', summary_path
        ]
        with self.assertRaises(CalledProcessError):
            subprocess_runner(log_level=logging.CRITICAL).run(cmd)
        cmd = [
            'mini_djerba.py', 'report',
            '--json', '/broken/json/path',
            '--out-dir', self.tmp_dir,
            '--ini', os.path.join(test_dir, 'mini_djerba.ini'),
            '--summary', summary_path
        ]
        with self.assertRaises(CalledProcessError):
            subprocess_runner(log_level=logging.CRITICAL).run(cmd)

    def test_report_work_dir(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        ini_path = os.path.join(test_dir, 'mini_djerba.ini')
        summary_path = os.path.join(test_dir, 'lorem.txt')
        work_dir = os.path.join(self.tmp_dir, 'work')
        os.mkdir(work_dir)
        cmd = [
            'mini_djerba.py', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--ini', ini_path,
            '--summary', summary_path,
            '--work-dir', work_dir
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_report(self.REPORT_MD5)

    def test_report_no_pdf(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        ini_path = os.path.join(test_dir, 'mini_djerba.ini')
        summary_path = os.path.join(test_dir, 'lorem.txt')
        cmd = [
            'mini_djerba.py', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--ini', ini_path,
            '--summary', summary_path,
            '--no-pdf'
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_report(self.REPORT_MD5, pdf=False)

    def test_report_no_summary(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        ini_path = os.path.join(test_dir, 'mini_djerba.ini')
        summary_path = os.path.join(test_dir, 'lorem.txt')
        cmd = [
            'mini_djerba.py', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--ini', ini_path
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_report(self.REPORT_NO_SUMMARY_MD5)

    def test_report_only_summary(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        summary_path = os.path.join(test_dir, 'lorem.txt')
        cmd = [
            'mini_djerba.py', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--summary', summary_path
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_report('a5449ca670301f8a022b1be1d0b76c9b')

    def test_report_no_change(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        cmd = [
            'mini_djerba.py', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_report('e4055904f20ec37adaf3b8d0d50d58d5')

    def test_setup(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        cmd = [
            'mini_djerba.py', 'setup',
            '--json', json_path,
            '--out-dir', self.tmp_dir
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        ini_file = os.path.join(self.tmp_dir, 'mini_djerba.ini')
        summary_file = os.path.join(self.tmp_dir, 'summary.txt')
        self.assert_setup(ini_file, summary_file)

    def test_setup_no_summary(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NO_SUMMARY)
        cmd = [
            'mini_djerba.py', 'setup',
            '--json', json_path,
            '--out-dir', self.tmp_dir
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        ini_file = os.path.join(self.tmp_dir, 'mini_djerba.ini')
        self.assert_setup(ini_file)


class Obsolete:

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

