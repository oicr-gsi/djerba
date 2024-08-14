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
            self.MD5: 'c1b89fcd4798c5471f3411a486878492'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.supplement.json")
        params = {
            self.INI: 'TAR.supp.ini',
            self.JSON: json_location,
            self.MD5: 'e81e3ece96ab5ddc5e3d24d02e9fa6dd'
        }
        self.run_basic_test(test_source_dir, params)
   
    def testTarFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.fail.supplement.json")
        params = {
            self.INI: 'TAR.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '7b113423d2a0a74feaf3f4777f8000c2'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarResearchSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.research.supplement.json")
        params = {
            self.INI: 'TAR.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: '93dcf07bba1facd7f1da21648a4a8960'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.supplement.json")
        params = {
            self.INI: 'WGTS.supp.ini',
            self.JSON: json_location,
            self.MD5: 'c1026f49ba0f6aa0065beed24795154a'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.fail.supplement.json")
        params = {
            self.INI: 'WGTS.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: 'e651df1a798250723496004e327df1ed'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsResearchSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.research.supplement.json")
        params = {
            self.INI: 'WGTS.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: 'eb747b1571dfa16511ef8c9507781eea'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.supplement.json")
        params = {
            self.INI: 'WGTS40X.supp.ini',
            self.JSON: json_location,
            self.MD5: 'ad79d76d9b6845fad08da990b16f118a'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XResearchSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.research.supplement.json")
        params = {
            self.INI: 'WGTS40X.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: 'b6ab576784f6bbfc180b82331b8e3dab'
        }
        self.run_basic_test(test_source_dir, params)


    def testWgts40XFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.fail.supplement.json")
        params = {
            self.INI: 'WGTS40X.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '33099524d413529141f80fe2d76d02ef'
            #self.MD5: '6f3fdb131ecbc0aad17622f34d2c11f8'
        }
        self.run_basic_test(test_source_dir, params)
    
if __name__ == '__main__':
    unittest.main()
