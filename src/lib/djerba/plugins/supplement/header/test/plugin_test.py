#! /usr/bin/env python3

"""Test of the supplement.header plugin"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester

class TestHeader(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'header.ini',
            self.JSON: 'header.json',
            self.MD5: '3fa3f2d86115f6c8a9da8063028e3564'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()

