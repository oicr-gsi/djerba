#! /usr/bin/env python3

"""Test of the demo1 plugin"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester

class TestDemo1(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'demo_1.ini',
            self.JSON: 'demo_1.json',
            self.MD5: '49199ee9117f159190e0d2ef41beff2e'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()

