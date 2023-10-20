"""
List of functions to convert MSI information into json format.
"""

# IMPORTS
import base64
import csv
import json
import logging
import os
import pandas as pd
import numpy
import djerba.plugins.genomic_landscape.constants as constants
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
from djerba.util.subprocess_runner import subprocess_runner
from djerba.plugins.tar.provenance_tools import parse_file_path
from djerba.plugins.tar.provenance_tools import subset_provenance
from statsmodels.distributions.empirical_distribution import ECDF

def run(self, work_dir, candidate_sites_path=None):
        if candidate_sites_path == None:
            candidate_sites_path = os.path.join(work, constants.MRDETECT_FILTER_ONLY_FILE_NAME)
        ctdna = {}
        ctdna[constants.CTDNA_CANDIDATES] = constants.extract_ctDNA_candidates(work_dir, candidate_sites_path)
        if ctdna[constants.CTDNA_CANDIDATES] >= constants.CTDNA_ELIGIBILITY_CUTOFF:
            ctdna[constants.CTDNA_ELIGIBILITY] = "eligible"
        elif ctdna[constants.CTDNA_CANDIDATES] < constants.CTDNA_ELIGIBILITY_CUTOFF:
            ctdna[constants.CTDNA_ELIGIBILITY] = "ineligible"
        else:
            self.logger.info("Discovered ctDNA candidates: {0}".format(ctdna[constants.CTDNA_CANDIDATES]))
            raise RuntimeError("Unknown number of candidates")
        return(ctdna)

def extract_ctDNA_candidates(self, work_dir, candidate_sites_path):
        with open(candidate_sites_path, 'r') as candidate_sites_file:
            reader_file = csv.reader(candidate_sites_file, delimiter="\t")
            for row in reader_file:
                try: 
                    candidates_sites_value = int(row[0])
                except IndexError as err:
                    msg = "Incorrect number of columns in mrdetect_filter_only row: '{0}'".format(row)+\
                          "read from '{0}'".format(os.path.join(work_dir, constants.MRDETECT_FILTER_ONLY_FILE_NAME))
                    self.logger.error(msg)
                    raise RuntimeError(msg) from err
        return candidates_sites_value
