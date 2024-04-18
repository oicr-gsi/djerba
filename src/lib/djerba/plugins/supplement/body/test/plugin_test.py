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
            self.MD5: '878c2defac8b85e2ca9000fa13479d03'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.supplement.json")
        params = {
            self.INI: 'TAR.supp.ini',
            self.JSON: json_location,
            self.MD5: '4ff388fc36cba071715101583eb467af'
        }
        self.run_basic_test(test_source_dir, params)
   
    def testTarFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.fail.supplement.json")
        params = {
            self.INI: 'TAR.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: 'b0b0c44835ff2055316f7df6408b8fa4'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.supplement.json")
        params = {
            self.INI: 'WGTS.supp.ini',
            self.JSON: json_location,
            self.MD5: 'bb7e1ce8b6af9fcd3003be6d8ad5f976'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.fail.supplement.json")
        params = {
            self.INI: 'WGTS.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '56f3eb5c6c662cf67e8a4fb8ea219f09'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.supplement.json")
        params = {
            self.INI: 'WGTS40X.supp.ini',
            self.JSON: json_location,
            self.MD5: '021ef28363c75a55b69ff9abd6167320'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.fail.supplement.json")
        params = {
            self.INI: 'WGTS40X.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '42e54fe6c150806d8d884d2c762957a1'
        }
        self.run_basic_test(test_source_dir, params)
    
if __name__ == '__main__':
    unittest.main()
