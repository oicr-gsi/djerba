"""General-purpose functions for WGTS plugins"""

import csv
import json
import logging
import os
import re
import djerba.core.constants as core_constants
from djerba.helpers.expression_helper.helper import main as expr_helper
from djerba.util.environment import directory_finder
from djerba.util.logger import logger
from djerba.util.oncokb.tools import levels as oncokb_levels

class wgts_tools(logger):

    CHROMOSOME = 'Chromosome'
    EXPRESSION_PERCENTILE = 'Expression percentile'
    HAS_EXPRESSION_DATA = 'Has expression data'
    BODY = 'Body'
    GENE = 'Gene'
    GENE_URL = 'Gene URL'
    ONCOKB = core_constants.ONCOKB
    UNKNOWN = 'Unknown'
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
        UNKNOWN
    ]

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.data_dir = directory_finder(log_level, log_path).get_data_dir()

    def cytoband_lookup(self):
        cytoband_path = os.path.join(self.data_dir, 'cytoBand.txt')
        cytobands = {}
        with open(cytoband_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                cytobands[row['Hugo_Symbol']] = row['Chromosome']
        return cytobands

    def cytoband_sort_order(self, cb_input):
        """
        Cytobands are (usually) of the form [integer][p or q][decimal]
        Also deal with edge cases
        """
        end = (999, 'z', 999999)
        if cb_input in self.UNCLASSIFIED_CYTOBANDS:
            msg = "Cytoband \"{0}\" is unclassified, ".format(cb_input)+\
                "moving to end of sort order"
            self.logger.debug(msg)
            (chromosome, arm, band) = end
        else:
            try:
                cb = re.split('\s+', cb_input).pop(0) # remove suffixes
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
                if re.match('^([0-9]+|[XY])[pq]', cb):
                    arm = re.split('[^pq]+', cb).pop(1)
                if re.match('^([0-9]+|[XY])[pq][0-9]+\.*\d*$', cb):
                    band = float(re.split('[^0-9\.]+', cb).pop(1))
            except (IndexError, ValueError) as err:
                # if error occurs in ordering, move to end of sort order
                msg = "Cannot parse cytoband \"{0}\" for sorting; ".format(cb_input)+\
                      "moving to end of sort order. No further action is needed. "+\
                      "Reason for parsing failure: {0}".format(err)
                self.logger.warning(msg)
                (chromosome, arm, band) = end
        return (chromosome, arm, band)

    @staticmethod
    def has_expression(work_dir):
        in_path = os.path.join(work_dir, expr_helper.TCGA_EXPR_PCT_JSON)
        return os.path.exists(in_path)

    @staticmethod
    def read_expression(work_dir):
        # read the expression metric from JSON written by the expression helper
        in_path = os.path.join(work_dir, expr_helper.TCGA_EXPR_PCT_JSON)
        with open(in_path) as in_file:
            expr = json.loads(in_file.read())
        # convert from strings to floats
        for key in expr.keys():
            expr[key] = float(expr[key])
        return expr

    def sort_variant_rows(self, rows):
        # sort rows oncokb level, then by cytoband, then by gene name
        rows = sorted(rows, key=lambda row: row[self.GENE])
        rows = sorted(rows, key=lambda row: self.cytoband_sort_order(row[self.CHROMOSOME]))
        rows = sorted(rows, key=lambda row: oncokb_levels.oncokb_order(row[self.ONCOKB]))
        return rows

