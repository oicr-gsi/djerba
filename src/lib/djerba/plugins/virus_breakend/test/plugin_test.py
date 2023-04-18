#! /usr/bin/env python3

"""
Test for VIRUSBreakend plugin.
"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester

class TestVirus(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'virus.ini',
            self.JSON: 'virus.json',
            self.MD5: 'e80ba5f5c94732b00def5bd30da4dd89'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
