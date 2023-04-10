#! /usr/bin/env python3

"""Test of the demo2 plugin"""

import os
import unittest
from djerba.plugins.plugin_test_base import PluginTester

class TestDemo2(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'demo_2.ini',
            self.JSON: 'demo_2.json',
            self.MD5: '24847a8739c68b7ead6b89552c89396d'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()

