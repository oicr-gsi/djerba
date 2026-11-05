"""Find and read expression values"""

import csv
import json
import logging
import os
from djerba.helpers.expression_helper.helper import main as expr_helper
from djerba.util.logger import logger
from djerba.util.validator import waiting_path_validator

class expression_reader(logger):

    EXPRESSION_PERCENTILE = 'Expression percentile'
    HAS_EXPRESSION_DATA = 'Has expression data'
    
    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
    
    def has_expression(self, work_dir):
        in_path = os.path.join(work_dir, expr_helper.TCGA_EXPR_PCT_JSON)
        validator = waiting_path_validator(self.log_level, self.log_path)
        return validator.input_path_exists(in_path)

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

    def warn_missing_expression(self, work_dir, expression, genes):
        missing = sorted(set(gene for gene in genes if gene not in expression))
        if len(missing) == 0:
            return
        # genes in the sample but not the TCGA reference, written by the expression helper
        unmatched_path = os.path.join(work_dir, expr_helper.TCGA_UNMATCHED)
        unmatched = set()
        if os.path.exists(unmatched_path):
            with open(unmatched_path) as in_file:
                unmatched = set(row[0] for row in csv.reader(in_file, delimiter="\t"))
        for gene in missing:
            if gene in unmatched:
                reason = 'gene symbol not found in TCGA comparator data'
            else:
                # absent from the sample results, or its gene ID is absent from the GEP reference
                reason = 'gene not found in sample expression data or GEP reference'
            msg = 'No expression percentile for reported gene {0}, '.format(gene)+\
                'will be displayed as NA: {0}'.format(reason)
            self.logger.warning(msg)
