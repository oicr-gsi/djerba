#! /usr/bin/env python3

import json
import logging
import os
import unittest
from copy import deepcopy
from subprocess import CalledProcessError
from time import strftime

from djerba.core.main import DjerbaVersionMismatchError
from djerba.plugins.patient_info.plugin import main as patient_info_plugin
from djerba.plugins.supplement.body.plugin import main as supplement_plugin
from djerba.util.mini.main import main
from djerba.util.mini.mdc import mdc, MDCFormatError
from djerba.util.testing.tools import TestBase
from djerba.util.subprocess_runner import subprocess_runner

class TestMDC(TestBase):

    SUPPLEMENT_EXPECTED = {
        supplement_plugin.REPORT_SIGNOFF_DATE: '2023/12/01',
        supplement_plugin.GENETICIST: supplement_plugin.GENETICIST_DEFAULT,
        supplement_plugin.GENETICIST_ID: supplement_plugin.GENETICIST_ID_DEFAULT
    }

    def test_read(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        test_file = os.path.join(test_dir, 'config.mdc')
        patient_info, supplement, text = mdc().read(test_file)
        self.assertEqual(patient_info, patient_info_plugin.PATIENT_DEFAULTS)
        self.assertEqual(supplement, self.SUPPLEMENT_EXPECTED)
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
        supplement = {
            supplement_plugin.REPORT_SIGNOFF_DATE: strftime('%Y/%m/%d'),
            supplement_plugin.GENETICIST: 'Jones, Jennifer',
            supplement_plugin.GENETICIST_ID: supplement_plugin.GENETICIST_ID_DEFAULT
        }
        mdc().write(out_path, patient_info, supplement, text)
        self.assertTrue(os.path.isfile(out_path))
        patient_info_new, supplement_new, text_new = mdc().read(out_path)
        self.assertEqual(patient_info, patient_info_new)
        self.assertEqual(patient_info_new['patient_name'], 'Smith, John')
        self.assertEqual(supplement, supplement_new)
        self.assertEqual(supplement[supplement_plugin.GENETICIST], 'Jones, Jennifer')
        self.assertEqual(text, text_new)

class TestMiniBase(TestBase):

    JSON_NAME = 'simple_report_for_update.json'

    def assert_MDC(self, out_path):
        self.assertTrue(os.path.isfile(out_path))
        with open(out_path) as out_file:
            contents = out_file.read()
        contents = contents.replace(strftime('%Y/%m/%d'), 'placeholder')
        self.assertEqual(self.getMD5_of_string(contents), '2ba55ae5caf797415ed484c7da04781d')

    def assert_render(self):
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        for out_path in [html_path, pdf_path]:
            self.assertTrue(os.path.isfile(out_path))
        with open(html_path) as html_file:
            original = html_file.read()
        redacted = self.redact_html(original)
        self.assertEqual(self.getMD5_of_string(redacted), 'c47495c3ea02347f08db8f1b214007d2')

    def assert_update(self):
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        json_out = os.path.join(self.tmp_dir, 'updated_report.json')
        for out_path in [html_path, pdf_path, json_out]:
            self.assertTrue(os.path.isfile(out_path))
        with open(html_path) as html_file:
            original = html_file.read()
        redacted = self.redact_html(original)
        self.assertEqual(self.getMD5_of_string(redacted), 'e9d286a4ee4672caa5402294f322f011')
        with open(json_out) as json_file:
            json_data = json.loads(json_file.read())
        self.assertEqual(json_data['core']['extract_time'], '2023-12-20_21:38:10Z')
        dob = json_data['plugins']['patient_info']['results']['patient_dob']
        self.assertEqual(dob, '1970/01/01')
        text = json_data['plugins']['summary']['results']['summary_text']
        expected_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed '+\
            'do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        self.assertEqual(text.strip(), expected_text)


class TestMain(TestMiniBase):

    class mock_args_setup:
        """Use instead of argparse to store params for testing"""

        def __init__(self, out_file, json):
            self.subparser_name = 'setup'
            self.json = json
            self.out = out_file
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    class mock_args_render:
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
        self.assert_MDC(out_file)

    def test_render(self):
        out_dir = self.tmp_dir
        test_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(test_dir, 'config_for_update.mdc')
        json_path = os.path.join(test_dir, self.JSON_NAME)
        pdf = True
        args = self.mock_args_render(json_path, self.tmp_dir, pdf)
        main(self.tmp_dir).run(args)
        self.assert_render()

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
        self.assert_update()

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
        self.assert_MDC(out_path)

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
        self.assert_render()

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
        self.assert_update()

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

