#! /usr/bin/env python3

import os
import unittest

from djerba.plugins.plugin_tester import PluginTester
from djerba.plugins.tar.status.plugin import main as status_plugin

class TestTarStatus(PluginTester):

    INI_NAME = 'status.ini'

    def test_status(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        json_ff = os.path.join(test_source_dir, 'status_FF.json')
                               
        params = {
            self.INI: self.INI_NAME,
            self.JSON: json_ff,
            self.MD5: '174901db896e2de1e4c48c96d0024109'
        }
        self.run_basic_test(test_source_dir, params)


        
if __name__ == '__main__':
    unittest.main()
