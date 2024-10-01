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

class data_builder:

    def __init__(self,  work_dir, assay, oncotree_uc):
        finder = directory_finder() # TODO configure logging
        base_dir = finder.get_base_dir()
        self.data_dir = finder.get_data_dir()
        self.r_script_dir = base_dir + "/plugins/tar/snv_indel/snv_indel_tools/Rscripts"
        self.work_dir = work_dir
        self.assay = assay
        self.cytoband_path = self.data_dir + "/cytoBand.txt"
        self.oncotree_uc = oncotree_uc
    
    def build_small_mutations_and_indels(self, mutations_file):
        """read in small mutations; output rows for oncogenic mutations"""
        rows = []
        mutation_expression = {}
        cytobands = self.read_cytoband_map()
        with open(mutations_file) as data_file:
            for input_row in csv.DictReader(data_file, delimiter="\t"):
                gene = input_row[sic.HUGO_SYMBOL_TITLE_CASE]
                cytoband = cytobands.get(gene, 'Unknown')
                protein = input_row[sic.HGVSP_SHORT]
                if 'splice' in input_row[sic.VARIANT_CLASSIFICATION].lower():
                    protein = 'p.? (' + input_row[sic.HGVSC] + ')'  
                row = {
                    sic.GENE: gene,
                    sic.GENE_URL: hb.build_gene_url(gene),
                    sic.CHROMOSOME: cytoband,
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
        rows = self.sort_variant_rows(rows)
        rows = oncokb_levels.filter_reportable(rows)
        return rows
 
    def cytoband_sort_order(self, cb_input):
        """Cytobands are (usually) of the form [integer][p or q][decimal]; also deal with edge cases"""
        end = (999, 'z', 999999)
        if cb_input in sic.UNCLASSIFIED_CYTOBANDS:
            msg = "Cytoband \"{0}\" is unclassified, moving to end of sort order".format(cb_input)
            #self.logger.debug(msg)
            (chromosome, arm, band) = end
        else:
            try:
                cb = re.split('\s+', cb_input).pop(0) # remove suffixes like 'alternate reference locus'
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
                #self.logger.warning(msg)
                (chromosome, arm, band) = end
        return (chromosome, arm, band)
    
    def is_null_string(self, value):
        if isinstance(value, str):
            return value in ['', sic.NA]
        else:
            msg = "Invalid argument to is_null_string(): '{0}' of type '{1}'".format(value, type(value))
            #self.logger.error(msg)
            raise RuntimeError(msg)

    def read_cytoband_map(self):
        input_path = self.cytoband_path
        cytobands = {}
        with open(input_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                cytobands[row[sic.HUGO_SYMBOL_TITLE_CASE]] = row['Chromosome']
        return cytobands

    def read_somatic_mutation_totals(self, mutations_file):
        # Count the somatic mutations
        # Splice_Region is *excluded* for TMB, *included* in our mutation tables and counts
        # Splice_Region mutations are of interest to us, but excluded from the standard TMB definition
        # The TMB mutation count is (independently) implemented and used in vaf_plot.R
        # See JIRA ticket GCGI-496
        total = 0
        with open(mutations_file) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                total += 1
        return total

    def reformat_level_string(self, level):
        return re.sub('LEVEL_', "", level)

    def sort_variant_rows(self, rows):
        # sort rows oncokb level, then by cytoband, then by gene name
        #self.logger.debug("Sorting rows by gene name")
        rows = sorted(rows, key=lambda row: row[sic.GENE])
        #self.logger.debug("Sorting rows by cytoband")
        rows = sorted(rows, key=lambda row: self.cytoband_sort_order(row[sic.CHROMOSOME]))
        #self.logger.debug("Sorting rows by oncokb level")
        rows = sorted(rows, key=lambda row: oncokb_levels.oncokb_order(row[sic.ONCOKB]))
        return rows
