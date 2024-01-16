#! /usr/bin/env python3

"""Test of the pwgs cardea helper"""

import logging
import os
import time
import unittest
from configparser import ConfigParser
import djerba.core.constants as core_constants
from djerba.core.loaders import helper_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase
from djerba.helpers.pwgs_cardea_helper.helper import main, \
    MissingCardeaError, WrongLibraryCodeError

class TestCardea(TestBase):

    CARDEA_URL='https://cardea.gsi.oicr.on.ca/requisition-cases'

    def testGetCardea(self):
        requisition_id = "PWGVAL_011418_Ct"
        requisition_info = main.get_cardea(self, requisition_id, self.CARDEA_URL)
        self.assertEqual(requisition_info["assay"], 'pWGS - 30X')
        self.assertEqual(requisition_info["project"], 'PWGVAL')
        self.assertEqual(requisition_info["provenance_id"], 'OCT_011418_Ct_T_nn_1-11_LB01-01')

    def test_getFakeRequisition(self):
        requisition_id = "BLURGY_123"
        self.assertRaises(MissingCardeaError, main.get_cardea, self, requisition_id, self.CARDEA_URL)

    def test_getWrongLibraryCode(self):
        requisition_id = "VAL_MYR_0098_WGS"
        self.assertRaises(WrongLibraryCodeError, main.get_cardea, self, requisition_id, self.CARDEA_URL)
        
if __name__ == '__main__':
    unittest.main() 