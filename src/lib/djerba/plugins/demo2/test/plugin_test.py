#! /usr/bin/env python3

"""Test of the demo2 plugin"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester

class TestDemo2(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(self.tmp_dir, 'question.txt'), 'w') as out_file:
            out_file.write('What do you get if you multiply six by nine?')
        params = {
            self.INI: 'demo_2.ini',
            self.JSON: 'demo_2.json',
            self.MD5: '26d45bf294d7c38694e4f04ca96b23c6'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()

