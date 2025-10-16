#! /usr/bin/env python3

"""Test of the patient info plugin"""

import json
import logging
import os
import unittest
import djerba.core.constants as cc
from djerba.core.workspace import workspace
from djerba.plugins.plugin_tester import PluginTester
from djerba.plugins.patient_info.plugin import main as patient_info_plugin

class TestPatientInfo(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'patient_info.ini',
            self.JSON: 'patient_info.json',
            self.MD5: 'bfd996505e729ec9b119c0b12afb8c21'
        }
        self.run_basic_test(test_source_dir, params)

    def test_redact(self):
        # test the redact method
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        kwargs = {
            cc.IDENTIFIER: 'patient_info',
            cc.MODULE_DIR: os.path.realpath(os.path.join(test_source_dir, '..')),
            cc.LOG_LEVEL: logging.WARNING,
            cc.LOG_PATH: None,
            cc.WORKSPACE: workspace(self.tmp_dir)
        }
        plugin = patient_info_plugin(**kwargs)
        with open(os.path.join(test_source_dir, 'patient_info.json')) as in_file:
            data = json.loads(in_file.read())
        redacted = plugin.redact(data)
        with open(os.path.join(test_source_dir, 'patient_info_redacted.json')) as in_file:
            expected = json.loads(in_file.read())
        self.assertEqual(redacted, expected)

if __name__ == '__main__':
    unittest.main()

