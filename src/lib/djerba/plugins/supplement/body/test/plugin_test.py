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
            self.MD5: 'f2b87a5e76c912de7bbc7cbcfc18b3a3'
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
            self.MD5: '25de723b077017ff5c6b859253890695'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgtsFailSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts.fail.supplement.json")
        params = {
            self.INI: 'WGTS.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '1e670c1638a9b0a5f55af3b3c4f81566'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgtsResearchSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts.research.supplement.json")
        params = {
            self.INI: 'WGTS.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: '5473cd1d60e40e638a8b9028d7de4cda'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.supplement.json")
        params = {
            self.INI: 'WGTS40X.supp.ini',
            self.JSON: json_location,
            self.MD5: 'f378a169abe1335deb2d897e57249f83'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XResearchSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.research.supplement.json")
        params = {
            self.INI: 'WGTS40X.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: '84f3a9c77ca6acdd5823d8a4f6a977ee'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XFailSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.fail.supplement.json")
        params = {
            self.INI: 'WGTS40X.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '16a0d82e015fd050852862046dd5606a'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)
    
if __name__ == '__main__':
    unittest.main()
