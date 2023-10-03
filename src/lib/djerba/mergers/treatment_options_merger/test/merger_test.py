#! /usr/bin/env python3

"""Test of the treatment options merger"""

import json
import logging
import os
import unittest
import djerba.core.constants as cc
from djerba.core.loaders import merger_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase
from djerba.mergers.treatment_options_merger.merger import main

class TestTreatmentOptionsMerger(TestBase):

    TREATMENT_OPTS_INPUTS = 'treatment_options_inputs.json'
    MODULE_NAME = 'treatment_options_merger'

    def test_gene_info(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_path = os.path.join(test_source_dir, self.TREATMENT_OPTS_INPUTS)
        with open(json_path) as json_file:
            inputs = json.loads(json_file.read())
        loader = merger_loader(logging.WARNING)
        merger = loader.load(self.MODULE_NAME)
        self.assertEqual(merger.ini_defaults.get(cc.CONFIGURE_PRIORITY), 300)
        self.assertEqual(merger.ini_defaults.get(cc.RENDER_PRIORITY), 50)
        html = merger.render(inputs)
        md5_found = self.getMD5_of_string(html)
        self.assertEqual(md5_found, '4f0efc5197fdd53b1197384a4dbe2305')

if __name__ == '__main__':
    unittest.main()
