"""
List of functions to convert sWGS information into json format.
AUTHOR: Aqsa Alam
"""

# IMPORTS
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

class data_builder:

  ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
  ONCOKB_LEVEL = 'OncoKB'
  ALTERATION_UPPER_CASE = 'ALTERATION'
  ONCOGENIC = 'ONCOGENIC'
  CNA_ANNOTATED = "data_CNA_oncoKBgenes_nonDiploid_annotated.txt"
  HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
  HUGO_SYMBOL_TITLE_CASE = 'Hugo_Symbol'
  NA = 'NA'

  UNCLASSIFIED_CYTOBANDS = [
    "", # some genes have an empty string for cytoband
    "mitochondria",
    "not on reference assembly",
    "reserved",
    "unplaced",
    "13cen",
    "13cen, GRCh38 novel patch",
    "2cen-q11",
    "2cen-q13",
    "c10_B",
    "HSCHR6_MHC_COXp21.32",
    "HSCHR6_MHC_COXp21.33",
    "HSCHR6_MHC_COXp22.1",
    "Unknown"
  ]

  def __init__(self, work_dir):

    # DIRECTORIES
    self.input_dir = "."
    finder = directory_finder() # TODO configure logging
    base_dir = finder.get_base_dir()
    self.r_script_dir = base_dir + "/plugins/tar/Rscripts/"
    self.work_dir = work_dir
    self.data_dir = finder.get_data_dir()
    self.cytoband_path = os.path.join(self.data_dir, 'cytoBand.txt')
    self.cytoband_map = self.read_cytoband_map()
    self.tmp_dir = work_dir + "/tmp"

  def build_swgs_rows(self):
    rows = []
    with open(os.path.join(self.work_dir, self.CNA_ANNOTATED)) as input_file:
        reader = csv.DictReader(input_file, delimiter="\t")
        for row in reader:
            gene = row[self.HUGO_SYMBOL_UPPER_CASE]
            cytoband = self.cytoband_map.get(gene, 'Unknown')
            if row[self.ALTERATION_UPPER_CASE] == "Amplification":
              row = {
                  constants.GENE: gene,
                  constants.GENE_URL: hb.build_gene_url(gene),
                  constants.ALTERATION: row[self.ALTERATION_UPPER_CASE],
                  constants.CHROMOSOME: cytoband,
                  constants.ONCOKB: oncokb_levels.parse_oncokb_level(row)
              }
              rows.append(row)
    rows = self.sort_variant_rows(rows)
    rows = oncokb_levels.filter_reportable(rows)
    return rows
    
   # --------------------------- ALL EXTRA FUNCTIONS ---------------------

  def read_cytoband_map(self):
    input_path = self.cytoband_path
    cytobands = {}
    with open(input_path) as input_file:
        reader = csv.DictReader(input_file, delimiter="\t")
        for row in reader:
            cytobands[row[self.HUGO_SYMBOL_TITLE_CASE]] = row['Chromosome']
    return cytobands
  
  def sort_variant_rows(self, rows):
    # sort rows oncokb level, then by cytoband, then by gene name
    #self.logger.debug("Sorting rows by gene name")
    rows = sorted(rows, key=lambda row: row[constants.GENE])
    #self.logger.debug("Sorting rows by cytoband")
    rows = sorted(rows, key=lambda row: self.cytoband_sort_order(row[constants.CHROMOSOME]))
    #self.logger.debug("Sorting rows by oncokb level")
    rows = sorted(rows, key=lambda row: oncokb_levels.oncokb_order(row[constants.ONCOKB]))
    return rows

  def cytoband_sort_order(self, cb_input):
    """Cytobands are (usually) of the form [integer][p or q][decimal]; also deal with edge cases"""
    end = (999, 'z', 999999)
    if cb_input in self.UNCLASSIFIED_CYTOBANDS:
        msg = "Cytoband \"{0}\" is unclassified, moving to end of sort order".format(cb_input)
        self.logger.debug(msg)
        (chromosome, arm, band) = end
    else:
        try:
            cb = re.split(r'\s+', cb_input).pop(0) # remove suffixes like 'alternate reference locus'
            cb = re.split('-', cb).pop(0) # take the first part of eg. 2q22.2-q22.3
            chromosome = re.split('[pq]', cb).pop(0)
            if chromosome == 'X':
                chromosome = 23
            elif chromosome == 'Y':
                chromosome = 24
            else:
                chromosome = int(chromosome)
            arm = 'a' # arm may be missing; default to beginning of sort order
            band = 0 # band may be missing; default to beginning of sort order
            if re.match(r'^([0-9]+|[XY])[pq]', cb):
                arm = re.split('[^pq]+', cb).pop(1)
            if re.match(r'^([0-9]+|[XY])[pq][0-9]+\.*\d*$', cb):
                band = float(re.split(r'[^0-9\.]+', cb).pop(1))
        except (IndexError, ValueError) as err:
            # if error occurs in ordering, move to end of sort order
            msg = "Cannot parse cytoband \"{0}\" for sorting; ".format(cb_input)+\
                    "moving to end of sort order. No further action is needed. "+\
                    "Reason for parsing failure: {0}".format(err)
            self.logger.info(msg)
            (chromosome, arm, band) = end
    return (chromosome, arm, band)
