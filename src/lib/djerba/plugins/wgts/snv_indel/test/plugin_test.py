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
from djerba.util.environment import directory_finder

class TestSnvIndelPlugin(PluginTester):

    INI_NAME = 'snv_indel.ini'
    JSON_NAME = 'snv_indel.json'
    JSON_NAME_NO_CNV = 'snv_indel_no_cnv.json'
    JSON_NAME_NO_MUT = 'snv_indel_no_somatic_mutations.json'
    
    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.sup_dir = directory_finder().get_test_dir()

    def testSnvIndelWithCNV(self):

        data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(data_dir_root, 'plugins', 'wgts', 'snv_indel')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        maf_filename = 'PANX_1391_Lv_M_WG_100-NH-020_LCM3.filter.deduped.realigned.'+\
            'recalibrated.mutect2.filtered.subset.maf.gz'
        maf_path = os.path.join(data_dir, maf_filename)
        expression_path = os.path.join(data_dir, 'data_expression_percentile_tcga.json')
        copy_number_path = os.path.join(data_dir, 'cn.txt')
        purity_ploidy_path = os.path.join(data_dir, 'purity_ploidy.json')
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute( {'MAF_PATH': maf_path})
        tmp_dir = self.get_tmp_dir()
        input_dir = os.path.join(tmp_dir, 'input')
        os.mkdir(input_dir)
        work_dir = os.path.join(tmp_dir, 'work')
        os.mkdir(work_dir)
        copy(copy_number_path, work_dir)
        copy(expression_path, work_dir)
        copy(purity_ploidy_path, work_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(os.path.join(data_dir, self.JSON_NAME), input_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME,
            self.MD5: '50e72522f6fac3c9566f55e5b740f275'
        }
        self.run_basic_test(input_dir, params, work_dir=work_dir)

    def testSnvIndelNoCNV(self):

        data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(data_dir_root, 'plugins', 'wgts', 'snv_indel')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        maf_filename = 'PANX_1391_Lv_M_WG_100-NH-020_LCM3.filter.deduped.realigned.'+\
            'recalibrated.mutect2.filtered.subset.maf.gz'
        maf_path = os.path.join(data_dir, maf_filename)
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
        copy(expression_path, work_dir)
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(os.path.join(data_dir, self.JSON_NAME_NO_CNV), input_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME_NO_CNV,
            self.MD5: '9de5fdf73e7c4186e859f6c2c06d86e1'
        }
        self.run_basic_test(input_dir, params, work_dir=work_dir)

    def testNoSomaticMutations(self):
        """
        Test on MYC_0279 example of a case where data_mutations_extended.txt is empty. 
        There should be no vaf plot.
        This is a WGS case, so no expression.
        """
        
        data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(data_dir_root, 'plugins', 'wgts', 'snv_indel')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        maf_filename = 'MYC_0279_Bm_P_WG_MyC-279-T0-OZ.mutect2.filtered.maf.gz'
        maf_path = os.path.join(data_dir, maf_filename)
        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        ini_str = template.substitute( {'MAF_PATH': maf_path})
        tmp_dir = self.get_tmp_dir()
        input_dir = os.path.join(tmp_dir, 'input')
        os.mkdir(input_dir)
        work_dir = os.path.join(tmp_dir, 'work')
        os.mkdir(work_dir)
        work_dir = '/.mounts/labs/CGI/scratch/aalam/examples/test/'
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        copy(os.path.join(data_dir, self.JSON_NAME_NO_MUT), input_dir)
        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME_NO_MUT,
            self.MD5: '88825ed6bbe5891ba7cfb920a372928f'
        }
        self.run_basic_test(input_dir, params, work_dir=work_dir)

    def redact_json_data(self, data):
        """replaces empty method from testing.tools"""
        del data['results']['vaf_plot']
        return data 

if __name__ == '__main__':
    unittest.main()
