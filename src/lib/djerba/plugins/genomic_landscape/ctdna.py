import csv
import logging
import os
import djerba.plugins.genomic_landscape.constants as constants
from djerba.util.logger import logger


class ctdna_processor(logger):

    def __init__(self, log_level, log_path):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def run(self, candidate_sites_path):
        candidates = self.extract_ctDNA_candidates(candidate_sites_path)
        if candidates >= constants.CTDNA_ELIGIBILITY_CUTOFF:
            eligibility = "eligible"
        else:
            eligibility = "ineligible"
        return self.get_results(candidates, eligibility)

    def extract_ctDNA_candidates(self, candidate_sites_path):
        rows = 0
        with open(candidate_sites_path, 'r') as candidate_sites_file:
            for row in csv.reader(candidate_sites_file, delimiter="\t"):
                rows += 1
                try:
                    candidates_sites_value = int(row[0])
                except IndexError as err:
                    msg = "Incorrect format for CTDNA file {0}; ".format(candidate_sites_path) + \
                          "should be a tab-delimited file with at least 1 column"
                    self.logger.error(msg)
                    raise RuntimeError(msg) from err
                except ValueError as err:
                    msg = "Incorrect CTDNA value: Expected integer, found {0}".format(row[0])
                    self.logger.error(msg)
                    raise RuntimeError(msg) from err
        if rows == 0:
            msg = "No rows found in CTDNA file {0}".format(candidate_sites_path)
            self.logger.error(msg)
            raise RuntimeError(msg)
        elif rows > 1:
            self.logger.warning("Expected 1 row in CTDNA file, found {0}".format(rows))
        return candidates_sites_value

    def get_dummy_results(self):
        # return placeholder values for when inputs are not available
        return self.get_results(0, 'eligibility unknown')

    def get_results(self, candidates, eligibility):
        # get a simple results data structure
        ctdna = {
            constants.CTDNA_CANDIDATES: candidates,
            constants.CTDNA_ELIGIBILITY: eligibility
        }
        return ctdna

