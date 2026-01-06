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
            self.MD5: 'bc01e729f1bcc66c70bcca9d171947a4'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testTarResearchSupplementary(self):
        json_location = os.path.join(self.ref_dir, "tar.research.supplement.json")
        params = {
            self.INI: 'TAR.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: 'e7326eebd92557665c975f705a09ab6b'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)
   
    def testTarFailSupplementary(self):
        json_location = os.path.join(self.ref_dir, "tar.fail.supplement.json")
        params = {
            self.INI: 'TAR.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '5b6bf63ddc517c95f36cb526bb8b463f'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgtsSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts.supplement.json")
        params = {
            self.INI: 'WGTS.supp.ini',
            self.JSON: json_location,
            self.MD5: '867b96003a7220eed61ba9275f42dcae'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgtsFailSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts.fail.supplement.json")
        params = {
            self.INI: 'WGTS.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '46bc9f364e52a6f0e4b03794a018d34c'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgtsResearchSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts.research.supplement.json")
        params = {
            self.INI: 'WGTS.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: '112bc0dd219899a5ceab41349ee882a5'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.supplement.json")
        params = {
            self.INI: 'WGTS40X.supp.ini',
            self.JSON: json_location,
            self.MD5: '98f0952d97753e6c63f4628fc646540d'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XResearchSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.research.supplement.json")
        params = {
            self.INI: 'WGTS40X.RESEARCH.supp.ini',
            self.JSON: json_location,
            self.MD5: '849471bda1f37ed877412d0a79906d3f'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)

    def testWgts40XFailSupplementary(self):
        json_location = os.path.join(self.ref_dir, "wgts40X.fail.supplement.json")
        params = {
            self.INI: 'WGTS40X.FAIL.supp.ini',
            self.JSON: json_location,
            self.MD5: '07a0ec0f5a4d9b4ff547e1f9ffdd90d2'
        }
        self.run_basic_test(self.test_source_dir, params, work_dir=self.work_dir)
    
if __name__ == '__main__':
    unittest.main()
