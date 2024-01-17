#! /usr/bin/env python3

"""Test of the supplement body plugin"""

import os
import unittest
import tempfile

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester

class TestSupplementaryPluginBody(PluginTester):
    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DIR'
        self.sup_dir = os.environ.get(sup_dir_var)

    def testPwgsSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/pwgs.supplement.json")
        params = {
            self.INI: 'PWGS.supp.ini',
            self.JSON: json_location,
            self.MD5: '9b8d57d6334c77646a1bdd03620a54db'
        }
        self.run_basic_test(test_source_dir, params)

    def testTarSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.supplement.json")
        params = {
            self.INI: 'TAR.supp.ini',
            self.JSON: json_location,
            self.MD5: '39b433a6599858cd7db8599b189e9a34'
        }
        self.run_basic_test(test_source_dir, params)
   
    def testTarFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/tar.fail.supplement.json")
        params = {
            self.INI: 'TAR.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '2835d2a22455d82984de7e3b4aba75af'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.supplement.json")
        params = {
            self.INI: 'WGTS.supp.ini',
            self.JSON: json_location,
            self.MD5: '6379cd10931c2ef069d50260d078e711'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgtsFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts.fail.supplement.json")
        params = {
            self.INI: 'WGTS.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '88ad09079832227902c7bb24753e3664'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.supplement.json")
        params = {
            self.INI: 'WGTS40X.supp.ini',
            self.JSON: json_location,
            self.MD5: 'd931634ef8bca2a29c751f0738167ff0'
        }
        self.run_basic_test(test_source_dir, params)

    def testWgts40XFailSupplementary(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(self.sup_dir ,"plugins/supplement/report_json/wgts40X.fail.supplement.json")
        params = {
            self.INI: 'WGTS40X.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '2428443f241be1ddb5a61b94ce2e35b8'
        }
        self.run_basic_test(test_source_dir, params)

if __name__ == '__main__':
    unittest.main()
