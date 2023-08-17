"""
List of functions to convert TAR SNV Indel information into json format.
"""

# IMPORTS
import base64
import csv
import json
import logging
import os
import re
import pandas as pd
from djerba.snv_indel_tools.extract import data_builder as sit
import djerba.snv_indel_tools.constants as sic
import djerba.cnv_tools.constants as cc
import djerba.render.constants as rc
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
import djerba.extract.oncokb.constants as oncokb
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.logger import logger

class data_builder(logger):

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir
        self.cytoband_path = os.environ.get('DJERBA_BASE_DIR') + sic.CYTOBAND

    def build_copy_number_variation(self, assay, cna_annotated_path):
            self.logger.debug("Building data for copy number variation table")
            rows = []
            if assay == "WGTS":
                mutation_expression = sit().read_expression()
                has_expression_data = True
            else:
                mutation_expression = {}
                has_expression_data = False
            with open(cna_annotated_path) as input_file:
                reader = csv.DictReader(input_file, delimiter="\t")
                for row in reader:
                    gene = row[sic.HUGO_SYMBOL_UPPER_CASE]
                    cytoband = sit().get_cytoband(gene)
                    row = {
                        rc.EXPRESSION_METRIC: mutation_expression.get(gene), # None for WGS assay
                        rc.GENE: gene,
                        rc.GENE_URL: sit().build_gene_url(gene),
                        rc.ALT: row[sic.ALTERATION_UPPER_CASE],
                        rc.CHROMOSOME: cytoband,
                        rc.ONCOKB: sit().parse_oncokb_level(row)
                    }
                    rows.append(row)
            unfiltered_cnv_total = len(rows)
            self.logger.debug("Sorting and filtering CNV rows")
            rows = list(filter(sit().oncokb_filter, sit().sort_variant_rows(rows)))
            data = {
                sic.HAS_EXPRESSION_DATA: has_expression_data,
                sic.TOTAL_VARIANTS: unfiltered_cnv_total,
                sic.CLINICALLY_RELEVANT_VARIANTS: len(rows),
                sic.BODY: rows
            }
            return data

