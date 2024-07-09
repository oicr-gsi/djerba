#! /usr/bin/env python3

"""Test of the demo2 plugin"""

import os
import unittest
from djerba.plugins.plugin_tester import PluginTester

class TestDemo2(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(self.tmp_dir, 'integer.txt'), 'w') as out_file:
            out_file.write('5')
        params = {
            self.INI: 'demo_2.ini',
            self.JSON: 'demo_2.json',
            self.MD5: '43b36554b8332afe4f42447af42192f4'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()

