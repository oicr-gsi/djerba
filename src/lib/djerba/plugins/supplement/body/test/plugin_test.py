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
            self.MD5: '8a958cc5924b86cb05a0d8ea94fd34cb'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.supplement.json")
        params = {
            self.INI: 'TAR.supp.ini',
            self.JSON: json_location,
            self.MD5: 'c0068f1b1d35ccb5272ee0ad466dc7ef'
        }
        self.run_basic_test(test_source_dir, params)
   
    def testTarFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.fail.supplement.json")
        params = {
            self.INI: 'TAR.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '5826fffc01fed3f879620ba04c9bf722'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.supplement.json")
        params = {
            self.INI: 'WGTS.supp.ini',
            self.JSON: json_location,
            self.MD5: 'a816f21ecf534ef34cac84158d634fda'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.fail.supplement.json")
        params = {
            self.INI: 'WGTS.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: 'd58bf41116e0c3e12ebb0bd72c11a865'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.supplement.json")
        params = {
            self.INI: 'WGTS40X.supp.ini',
            self.JSON: json_location,
            self.MD5: '8a6b8c07b65ce541f2bff2ae35be2252'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.fail.supplement.json")
        params = {
            self.INI: 'WGTS40X.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: 'd02e5a70b7e2ca6e388b75c2030d50bf'
        }
        self.run_basic_test(test_source_dir, params)
    
if __name__ == '__main__':
    unittest.main()
