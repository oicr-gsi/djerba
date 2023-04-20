#! /usr/bin/env python3

"""Test of the demo1 plugin"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester

class TestSnvIndel(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        params = {
            self.INI: 'snv_indel.ini',
            self.JSON: 'snv_indel.json',
            self.MD5: 'f9e24db7586da60dede22327a244e7d7'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()

