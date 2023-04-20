#! /usr/bin/env python3

"""Test of the demo1 plugin"""

import os
import unittest
from string import Template
from djerba.plugins.plugin_tester import PluginTester

class TestSnvIndel(PluginTester):

    def test(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(test_source_dir, 'snv_indel.ini')) as ini_file:
            ini_template = ini_file.read()
        mapping = {
            'DJERBA_TEST_DATA': os.environ.get('DJERBA_TEST_DATA')
        }
        ini_string = Template(ini_template).substitute(mapping)
        test_ini_path = os.path.join(self.tmp_dir, 'test.ini')
        with open(test_ini_path, 'w') as out_file:
            out_file.write(ini_string)
        expected_json_path = os.path.join(test_source_dir, 'snv_indel.json')
        expected_md5 = 'c3550d07cfc641fb2426e0a078452143'
        self.run_basic_test_from_paths(test_ini_path, expected_json_path, expected_md5)

if __name__ == '__main__':
    unittest.main()

