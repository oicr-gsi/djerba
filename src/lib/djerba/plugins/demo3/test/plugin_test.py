#! /usr/bin/env python3

"""Test of the demo2 plugin"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester

class TestDemo3(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'demo_3.ini',
            self.JSON: 'demo_3.json',
            self.MD5: 'e76838b1f7177af77d8206490a022730'
        }
        self.run_basic_test(test_source_dir, params, 'demo3')

if __name__ == '__main__':
    unittest.main()

