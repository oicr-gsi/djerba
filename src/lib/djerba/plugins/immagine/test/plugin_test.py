#! /usr/bin/env python3

"""Test of the PARPi table plugin"""

import os
import unittest
import tempfile
import string
import shutil
from djerba.util.validator import path_validator
from djerba.plugins.plugin_tester import PluginTester
from djerba.core.workspace import workspace
from djerba.util.environment import directory_finder

class TestImmaginePlugin(PluginTester):

    INI_NAME = 'test.ini'
    JSON_NAME = 'immagine.json'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)

        self.data_CNA = os.path.join(self.sup_dir, "plugins/immagine/purple.data_CNA.txt")
        self.data_mutations = os.path.join(self.sup_dir, "plugins/immagine/data_mutations_extended.txt")
        self.data_expression = os.path.join(self.sup_dir, "plugins/immagine/data_expression_percentile_tcga.txt")
        self.purity_ploidy = os.path.join(self.sup_dir, "plugins/immagine/purity_ploidy.json")
        self.purple_dir = os.path.join(self.sup_dir, "plugins/immagine/PLACEHOLDER.solPrimary.purple/")

    def testImmagine(self):
        data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(data_dir_root, 'plugins', 'immagine')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        igcaller_filename = 'PLACEHOLDER.filter.deduped.recalibrated_IgCaller.zip'
        igcaller_path = os.path.join(data_dir, igcaller_filename)
        
        sbs_filename = 'PLACEHOLDER.exposures.SBS.json' 
        sbs_path = os.path.join(data_dir, sbs_filename)

        with open(os.path.join(test_source_dir, self.INI_NAME)) as in_file:
            template_str = in_file.read()
        template = string.Template(template_str)
        
        # Ini string replacements
        # Ini string replacements
        ini_str = template.substitute({
            'IGCALLER_PATH': igcaller_path,
            'SBS_PATH': sbs_path
        })
        tmp_dir = self.get_tmp_dir()
        input_dir = os.path.join(tmp_dir, 'input')
        os.mkdir(input_dir)
        work_dir = os.path.join(tmp_dir, 'work')
        os.mkdir(work_dir)
        
        # Copy all the paths to the working directory
        for path in [self.data_CNA, self.data_mutations, self.data_expression, self.purity_ploidy]:
            shutil.copy(path, work_dir)
        shutil.copytree(
                self.purple_dir,
                os.path.join(work_dir, os.path.basename(self.purple_dir.rstrip('/')))
        )
        
        with open(os.path.join(input_dir, self.INI_NAME), 'w') as ini_file:
            ini_file.write(ini_str)
        shutil.copy(os.path.join(data_dir, self.JSON_NAME), input_dir)

        params = {
            self.INI: self.INI_NAME,
            self.JSON: self.JSON_NAME,
            self.MD5: 'f10fac7f51f2d5277e8ee197073d4f84'
        }
        self.run_basic_test(input_dir, params, work_dir=work_dir)

if __name__ == '__main__':
    unittest.main()
