#! /usr/bin/env python3

import json
import logging
import os
import unittest
from configparser import ConfigParser
from subprocess import CalledProcessError

import djerba.util.mini.constants as constants
from djerba.util.mini.main import main, MiniDjerbaScriptError
from djerba.util.testing.tools import TestBase
from djerba.util.subprocess_runner import subprocess_runner

class TestMiniBase(TestBase):

    JSON_NAME = 'simple_report_for_update.json'
    JSON_NO_SUMMARY = 'simple_report_no_summary.json'
    REPORT_MD5 = '4e40169d5ba33d4509681a7ee8831893'
    REPORT_NO_SUMMARY_MD5 = '8c8b57ed19c35ee6dd1782656691c867'

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

    MINI_DJERBA_EXECUTABLE = 'mini_djerba.py'

    def set_executable(self, exec_path):
        self.MINI_DJERBA_EXECUTABLE = exec_path

    def test_report(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        ini_path = os.path.join(test_dir, 'mini_djerba.ini')
        summary_path = os.path.join(test_dir, 'lorem.txt')
        cmd = [
            self.MINI_DJERBA_EXECUTABLE, '-v', 'report',
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
            self.MINI_DJERBA_EXECUTABLE, '-v', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--ini', os.path.join(test_dir, 'mini_djerba_broken_1.ini'),
            '--summary', summary_path
        ]
        with self.assertRaises(CalledProcessError):
            subprocess_runner(log_level=logging.CRITICAL).run(cmd)
        cmd = [
            self.MINI_DJERBA_EXECUTABLE, '-v', 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--ini', os.path.join(test_dir, 'mini_djerba_broken_2.ini'),
            '--summary', summary_path
        ]
        with self.assertRaises(CalledProcessError):
            subprocess_runner(log_level=logging.CRITICAL).run(cmd)
        cmd = [
            self.MINI_DJERBA_EXECUTABLE, '-v', 'report',
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
            self.MINI_DJERBA_EXECUTABLE, 'report',
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
            self.MINI_DJERBA_EXECUTABLE, 'report',
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
            self.MINI_DJERBA_EXECUTABLE, 'report',
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
            self.MINI_DJERBA_EXECUTABLE, 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--summary', summary_path
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_report('5d483a2283fce6ec3f92d60eac5185eb')

    def test_report_no_change(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, self.JSON_NAME)
        cmd = [
            self.MINI_DJERBA_EXECUTABLE, 'report',
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
            self.MINI_DJERBA_EXECUTABLE, 'setup',
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
            self.MINI_DJERBA_EXECUTABLE, 'setup',
            '--json', json_path,
            '--out-dir', self.tmp_dir
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        ini_file = os.path.join(self.tmp_dir, 'mini_djerba.ini')
        self.assert_setup(ini_file)

    def test_version_mismatch(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(test_dir, 'version_mismatch_report.json')
        ini_path = os.path.join(test_dir, 'mini_djerba.ini')
        cmd = [
            self.MINI_DJERBA_EXECUTABLE, 'report',
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--ini', ini_path
        ]
        with self.assertRaises(CalledProcessError):
            subprocess_runner(log_level=logging.CRITICAL).run(cmd)
        cmd.append('--force')
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assert_report('9ee14ad2eb58d55a5d3db33ec18dab7e')


if __name__ == '__main__':
    unittest.main()

