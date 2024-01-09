#! /usr/bin/env python3

import logging
import os
import unittest

from djerba.plugins.patient_info.plugin import main as patient_info_plugin
from djerba.util.mini.main import main
from djerba.util.mini.mdc import mdc, MDCFormatError
from djerba.util.testing.tools import TestBase

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

if __name__ == '__main__':
    unittest.main()

