#! /usr/bin/env python3

"""Test of the gene information merger"""

import json
import logging
import os
import unittest
import djerba.core.constants as cc
from configparser import ConfigParser
from djerba.core.loaders import merger_loader
from djerba.core.workspace import workspace
from djerba.util.testing.tools import TestBase
from djerba.mergers.gene_information_merger.merger import main

class TestGeneInformationMerger(TestBase):

    GENE_INFO_INPUTS = 'gene_information_inputs.json'
    MODULE_NAME = 'gene_information_merger'

    def test_gene_info(self):
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_path = os.path.join(test_source_dir, self.GENE_INFO_INPUTS)
        with open(json_path) as json_file:
            inputs = json.loads(json_file.read())
        loader = merger_loader(logging.WARNING)
        merger = loader.load(self.MODULE_NAME)
        self.assertEqual(merger.ini_defaults.get(cc.CONFIGURE_PRIORITY), 300)
        self.assertEqual(merger.ini_defaults.get(cc.RENDER_PRIORITY), 300)
        merger.set_priority_defaults(500)
        self.assertEqual(merger.ini_defaults.get(cc.CONFIGURE_PRIORITY), 500)
        self.assertEqual(merger.ini_defaults.get(cc.RENDER_PRIORITY), 500)
        html = merger.render(inputs)
        md5_found = self.getMD5_of_string(html)
        self.assertEqual(md5_found, 'd436df8d05a8af3cbdf71a15eb12f7ea')

if __name__ == '__main__':
    unittest.main()
