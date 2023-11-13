#! /usr/bin/env python3

"""Test of the provenance helper"""

import logging
import os
import time
import unittest
from configparser import ConfigParser
import djerba.core.constants as core_constants
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase
import djerba.helpers.pwgs_provenance_helper.helper as pwgs_helper

class TestCardea(TestBase):

    def test(self):
        self.CARDEA_URL='https://cardea.gsi.oicr.on.ca/requisition-cases'
        requisition_id = "PWGVAL_011418_Ct"
        requisition_info = pwgs_helper.main.get_cardea(self, requisition_id)
        self.assertEqual(requisition_info["assay_name"], 'pWGS - 30X')
        self.assertEqual(requisition_info["project"], 'PWGVAL')
        self.assertEqual(requisition_info["group_id"], 'OCT_011418_Ct_T_nn_1-11_LB01')
       
if __name__ == '__main__':
    unittest.main() 
