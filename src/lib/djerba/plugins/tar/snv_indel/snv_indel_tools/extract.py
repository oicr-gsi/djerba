import base64
import csv
import json
import logging
import os
import re
import pandas as pd
import djerba.plugins.tar.snv_indel.snv_indel_tools.constants as sic
from djerba.util.environment import directory_finder
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
from djerba.util.html import html_builder as hb
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.variant_sorter import variant_sorter

class data_builder(logger):

    def __init__(self, work_dir, assay, oncotree_uc, log_level, log_path):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.log_level = log_level
        self.log_path = log_path
        finder = directory_finder()
        base_dir = finder.get_base_dir()
        self.data_dir = finder.get_data_dir()
        self.work_dir = work_dir
        self.assay = assay
        self.oncotree_uc = oncotree_uc
    
    def build_small_mutations_and_indels(self, mutations_file):
        """read in small mutations; output rows for oncogenic mutations"""
        rows = []
        mutation_expression = {}
        var_sorter = variant_sorter(self.log_level, self.log_path) 
        cytobands = var_sorter.cytoband_lookup()
        with open(mutations_file) as data_file:
            for input_row in csv.DictReader(data_file, delimiter="\t"):
                gene = input_row[sic.HUGO_SYMBOL_TITLE_CASE]
                if gene in ['', 'NA', 'None']:
                    continue
                protein = input_row[sic.HGVSP_SHORT]
                if 'splice' in input_row[sic.VARIANT_CLASSIFICATION].lower():
                    protein = 'p.? (' + input_row[sic.HGVSC] + ')'  
                row = {
                    sic.GENE: gene,
                    sic.GENE_URL: hb.build_gene_url(gene),
                    sic.CHROMOSOME: cytobands.get(gene, 'Unknown'),
                    sic.PROTEIN: protein,
                    sic.PROTEIN_URL: hb.build_alteration_url(gene, protein, self.oncotree_uc),
                    sic.MUTATION_TYPE: re.sub('_', ' ', input_row[sic.VARIANT_CLASSIFICATION]),
                    sic.EXPRESSION_METRIC: mutation_expression.get(gene), # None for WGS assay
                    sic.VAF_PERCENT: int(round(float(input_row[sic.TUMOUR_VAF]), 2)*100),
                    sic.TUMOUR_DEPTH: int(input_row[sic.TUMOUR_DEPTH]),
                    sic.TUMOUR_ALT_COUNT: int(input_row[sic.TUMOUR_ALT_COUNT]),
                    sic.ONCOKB: oncokb_levels.parse_oncokb_level(input_row)
                }

                rows.append(row)
        rows = var_sorter.sort_variant_rows(rows)
        rows = oncokb_levels.filter_reportable(rows)
        return rows

    def read_somatic_mutation_totals(self, mutations_file):
        # Count the somatic mutations
        # Splice_Region is *excluded* for TMB, *included* in our mutation tables and counts
        # Splice_Region mutations are of interest to us, but excluded from the standard TMB definition
        # The TMB mutation count is (independently) implemented and used in vaf_plot.R
        # See JIRA ticket GCGI-496
        total = 0
        with open(mutations_file) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                if row[sic.HUGO_SYMBOL_TITLE_CASE] in ['', 'NA', 'None']:
                    continue
                total += 1
        return total
