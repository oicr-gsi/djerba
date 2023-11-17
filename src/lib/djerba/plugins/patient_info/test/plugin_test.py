#! /usr/bin/env python3

"""Test of the patient info plugin"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester

class TestPatientInfo(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'patient_info.ini',
            self.JSON: 'patient_info.json',
            self.MD5: 'd5af3273925ac2016e21e8570a2cc6ea'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()

