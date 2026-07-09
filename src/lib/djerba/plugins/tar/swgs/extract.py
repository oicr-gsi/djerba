"""
List of functions to convert sWGS information into json format.
AUTHOR: Aqsa Alam
"""

import base64
import csv
import json
import logging
import os
import re
import pandas as pd
from shutil import rmtree
import djerba.plugins.tar.swgs.constants as constants
from djerba.plugins.tar.swgs.preprocess import preprocess
from djerba.util.environment import directory_finder
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.html import html_builder as hb
from djerba.util.variant_sorter import variant_sorter

class data_builder(logger):

  ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
  ONCOKB_LEVEL = 'OncoKB'
  ALTERATION_UPPER_CASE = 'ALTERATION'
  CNA_ANNOTATED = "data_CNA_oncoKBgenes_nonDiploid_annotated.txt"
  HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
  NA = 'NA'

  def __init__(self, work_dir, log_level, log_path):
    self.logger = self.get_logger(log_level, __name__, log_path)
    self.log_level = log_level
    self.log_path = log_path
    finder = directory_finder() # TODO configure logging
    self.work_dir = work_dir

  def build_swgs_rows(self):
    rows = []
    var_sorter = variant_sorter(self.log_level, self.log_path) 
    cytobands = var_sorter.cytoband_lookup()
    with open(os.path.join(self.work_dir, self.CNA_ANNOTATED)) as input_file:
        reader = csv.DictReader(input_file, delimiter="\t")
        for row in reader:
            gene = row[self.HUGO_SYMBOL_UPPER_CASE]
            if row[self.ALTERATION_UPPER_CASE] == "Amplification":
              row = {
                  constants.GENE: gene,
                  constants.GENE_URL: hb.build_gene_url(gene),
                  constants.ALTERATION: row[self.ALTERATION_UPPER_CASE],
                  constants.CHROMOSOME: cytobands.get(gene, 'Unknown'),
                  constants.ONCOKB: oncokb_levels.parse_oncokb_level(row)
              }
              rows.append(row)
    rows = var_sorter.sort_variant_rows(rows)
    rows = oncokb_levels.filter_reportable(rows)
    return rows
