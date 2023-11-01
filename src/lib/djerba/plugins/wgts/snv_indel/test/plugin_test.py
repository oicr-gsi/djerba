#! /usr/bin/env python3

"""
Test of the WGTS SNV/indel plugin
"""

import os
import unittest
import string
import tempfile
from shutil import copy
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
import djerba.plugins.wgts.snv_indel.plugin as snv_indel
from djerba.core.workspace import workspace

class TestSnvIndelPlugin(PluginTester):

    INI_NAME = 'snv_indel.ini'
    JSON_NAME = 'snv_indel.json'

    def testSnvIndel(self):

        sup_dir = os.environ.get('DJERBA_TEST_DATA')
        data_dir = os.path.join(sup_dir, 'plugins', 'wgts', 'snv_indel')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        maf_filename = 'PANX_1391_Lv_M_WG_100-NH-020_LCM3.filter.deduped.realigned.'+\
            'recalibrated.mutect2.filtered.subset.maf.gz'
        maf_path = os.path.join(data_dir, maf_filename)
        copy_state_path = os.path.join(data_dir, 'copy_states.json')
        expression_path = os.path.join(data_dir, 'data_expression_percentile_tcga.json')
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute( {'MAF_PATH': maf_path})
        tmp_dir = self.get_tmp_dir()
        input_dir = os.path.join(tmp_dir, 'input')
        os.mkdir(input_dir)
        work_dir = os.path.join(tmp_dir, 'work')
        os.mkdir(work_dir)
        copy(copy_state_path, work_dir)
        copy(expression_path, work_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(os.path.join(data_dir, self.JSON_NAME), input_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME,
            self.MD5: '02fe420e3ffd2c25b9876c75c3c0d567'
        }
        self.run_basic_test(input_dir, params, work_dir=work_dir)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        del data['plugins']['wgts.snv_indel']['results']['vaf_plot']
        return data 

if __name__ == '__main__':
    unittest.main()
