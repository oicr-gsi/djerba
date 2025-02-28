#! /usr/bin/env python3

import os
import unittest

from configparser import ConfigParser
from djerba.plugins.plugin_tester import PluginTester
from djerba.plugins.tar.status.plugin import main as status_plugin

class TestTarStatus(PluginTester):

    INI_NAME_FF = 'status.ini'
    INI_NAME_TF = 'status_tf.ini'
    INI_NAME_FT = 'status_ft.ini'
    INI_NAME_TT = 'status_tt.ini'

    def test_status(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))        
        json_ff = os.path.join(test_source_dir, 'status_FF.json')
        params = {
            self.INI: self.INI_NAME_FF,
            self.JSON: json_ff,
            self.MD5: '174901db896e2de1e4c48c96d0024109'
        }
        self.run_basic_test(test_source_dir, params)
        # now run more tests, with different permutations of True/False inputs
        cp = ConfigParser()
        cp.read(os.path.join(test_source_dir, self.INI_NAME_FF))
        tmp = self.get_tmp_dir()
        # CNV = True, SNV = False
        cp.set('tar.status', 'copy_number_ctdna_detected', 'True')
        ini_path_tf = os.path.join(tmp, self.INI_NAME_TF)
        with open(ini_path_tf, 'w') as out_file:
            cp.write(out_file)
        params = {
            self.INI: ini_path_tf,
            self.JSON: os.path.join(test_source_dir, 'status_TF.json'),
            self.MD5: 'cfba59ac799700366c8639a067b65e7a'
        }
        self.run_basic_test(test_source_dir, params)
        


        
if __name__ == '__main__':
    unittest.main()
