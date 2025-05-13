#! /usr/bin/env python3

"""Test of the supplement body plugin"""

import os
import unittest
import tempfile
from copy import deepcopy
from shutil import copy

from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.util.environment import directory_finder

class TestSupplementaryPluginBody(PluginTester):

    def redact_json_data(self, data):
        redacted = deepcopy(data)
        redacted['results']['components']['core']['version'] = 'PLACEHOLDER'
        redacted['results']['template_dir'] = 'PLACEHOLDER'
        return redacted

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.work_dir = os.path.join(self.tmp_dir, 'work')
        os.mkdir(self.work_dir)
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))
        # copy a dummy component info JSON to the working directory
        component_info_path = os.path.join(self.test_source_dir, 'component_info.json')
        copy(component_info_path, self.work_dir)
        test_dir = directory_finder().get_test_dir()
        self.ref_dir = os.path.join(test_dir, 'plugins', 'supplement', 'report_json')

    def testPwgsSupplementary(self):
        json_location = os.path.join(self.ref_dir, "pwgs.supplement.json")
        params = {
            self.INI: 'PWGS.supp.ini',
            self.JSON: json_location,
            self.MD5: 'f808bc34cb7f88c48c4451d96f60ef9b'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testTarResearchSupplementary(self):
        json_location = os.path.join(self.ref_dir, "tar.research.supplement.json")
        params = {
            self.INI: 'TAR.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: 'c5ceb981bd6a9198866e53ac9d11d2ee'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)
   
    def testTarFailSupplementary(self):
        json_location = os.path.join(self.ref_dir, "tar.fail.supplement.json")
        params = {
            self.INI: 'TAR.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: 'f596822789e57599577d82d928401566'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgtsSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts.supplement.json")
        params = {
            self.INI: 'WGTS.supp.ini',
            self.JSON: json_location,
            self.MD5: '075c4e5b37369ebdbadcb8c7e17bc7de'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgtsFailSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts.fail.supplement.json")
        params = {
            self.INI: 'WGTS.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '66528ae63f7fea11e7a8c891f25838cb'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgtsResearchSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts.research.supplement.json")
        params = {
            self.INI: 'WGTS.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: 'f5321dd97599e69717ecd1aed5111dd4'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.supplement.json")
        params = {
            self.INI: 'WGTS40X.supp.ini',
            self.JSON: json_location,
            self.MD5: '4c2039342cec6c7897883f2a5d1566a6'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XResearchSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.research.supplement.json")
        params = {
            self.INI: 'WGTS40X.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: '2cba8af4f8c43b752113219e7860bc42'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XFailSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.fail.supplement.json")
        params = {
            self.INI: 'WGTS40X.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: 'e1b1e4f249f30c5c7c0c6180704d25f7'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)
    
if __name__ == '__main__':
    unittest.main()
