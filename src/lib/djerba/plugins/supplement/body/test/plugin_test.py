#! /usr/bin/env python3

"""Test of the supplement body plugin"""

import os
import unittest
import tempfile

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.environment import directory_finder

class TestSupplementaryPluginBody(PluginTester):
    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()

    def testPwgsSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/pwgs.supplement.json")
        params = {
            self.INI: 'PWGS.supp.ini',
            self.JSON: json_location,
            self.MD5: 'e0b00fdce6e91f9b5be4feeb8bd5e275'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.supplement.json")
        params = {
            self.INI: 'TAR.supp.ini',
            self.JSON: json_location,
            self.MD5: '6409990b8d72413cafc691f5783cdca4'
        }
        self.run_basic_test(test_source_dir, params)
   
    def testTarFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.fail.supplement.json")
        params = {
            self.INI: 'TAR.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '232bd372777958ff8b2982dbfd683c6b'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.supplement.json")
        params = {
            self.INI: 'WGTS.supp.ini',
            self.JSON: json_location,
            self.MD5: 'a1152e753b3cf5de3d3700334c003e1d'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.fail.supplement.json")
        params = {
            self.INI: 'WGTS.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '885f7a0c6a629d759fd1e0fd18fd932e'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.supplement.json")
        params = {
            self.INI: 'WGTS40X.supp.ini',
            self.JSON: json_location,
            self.MD5: '79f00ade151cbdc1ef8a0e825e31f102'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.fail.supplement.json")
        params = {
            self.INI: 'WGTS40X.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '25b2ef09bf5d0ef5bb8bc3caa658334e'
        }
        self.run_basic_test(test_source_dir, params)
    
if __name__ == '__main__':
    unittest.main()
