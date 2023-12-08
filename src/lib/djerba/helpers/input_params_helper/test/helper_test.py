#! /usr/bin/env python3

"""
Test of the input params helper
"""

import logging
import os
import unittest
from configparser import ConfigParser
from shutil import copy
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase

class InputParamsHelper(TestBase):

    CORE = 'core'
    HELPER_NAME = 'input_params_helper'
    INPUT_PARAMS_MD5 = '3f882da7af12b319cdfbf52188b6f078'

    def test_extract(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        
        # Get the config
        cp = ConfigParser()
        cp.read(os.path.join(test_source_dir, 'helper.ini'))
        
        loader = helper_loader(logging.WARNING)
        
        # Get the workspace 
        ws = workspace(self.tmp_dir)

        helper_main = loader.load(self.HELPER_NAME, ws)

        # Run configure step
        helper_main.configure(cp)

        # Get the input_params.json path that was just generated
        input_params_path = os.path.join(self.tmp_dir, 'input_params.json')  
        
        # Check if the input_params.json path exists
        self.assertTrue(os.path.exists(input_params_path))

        # Compare it against the md5 of the expected input_params.json
        self.assertEqual(self.getMD5(input_params_path), self.INPUT_PARAMS_MD5)


if __name__ == '__main__':
    unittest.main()
