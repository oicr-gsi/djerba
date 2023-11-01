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
import djerba.util.oncokb.constants as oncokb
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
        if os.path.exists(os.path.join(self.work_dir, sic.CNA_SIMPLE)):
            self.data_CNA_exists = True
        else:
            self.data_CNA_exists = False
        with open(os.path.join(work_dir, 'purity.txt'), "r") as file:
            self.purity = float(file.readlines()[0])

    def build_small_mutations_and_indels(self, mutations_file):
        """read in small mutations; output rows for oncogenic mutations"""
        rows = []
        all_reported_variants = set()
        if self.data_CNA_exists:
            mutation_copy_states = self.read_mutation_copy_states()
        mutation_expression = {}
        with open(mutations_file) as data_file:
            for input_row in csv.DictReader(data_file, delimiter="\t"):
                gene = input_row[sic.HUGO_SYMBOL_TITLE_CASE]
                cytoband = self.get_cytoband(gene)
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
                    sic.ONCOKB: self.parse_oncokb_level(input_row)
                }

                if self.purity >= 0.1 and self.data_CNA_exists:
                    row[sic.COPY_STATE] = mutation_copy_states.get(gene, sic.UNKNOWN)

                rows.append(row)
        rows = list(filter(self.oncokb_filter, self.sort_variant_rows(rows)))
        for row in rows: 
            all_reported_variants.add((row.get(sic.GENE), row.get(sic.CHROMOSOME)))
            row[sic.ONCOKB] = self.change_oncokb_level_name(row[sic.ONCOKB])
        return rows
 
    def change_oncokb_level_name(self, level):
        onc = 'Oncogenic'
        l_onc = 'Likely Oncogenic'
        p_onc = 'Predicted Oncogenic'
        
        if level == onc:
            level = 'N1'
        elif level == l_onc:
            level = 'N2'
        elif level == p_onc:
            level = 'N3'
        return level
    
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

    def get_cytoband(self, gene_name):
        cytoband_map = self.read_cytoband_map()
        cytoband = cytoband_map.get(gene_name)
        if not cytoband:
            cytoband = 'Unknown'
            msg = "Cytoband for gene '{0}' not found in {1}".format(gene_name, self.cytoband_path)
            #self.logger.info(msg)
        return cytoband
    
    def is_null_string(self, value):
        if isinstance(value, str):
            return value in ['', sic.NA]
        else:
            msg = "Invalid argument to is_null_string(): '{0}' of type '{1}'".format(value, type(value))
            #self.logger.error(msg)
            raise RuntimeError(msg)

    def oncokb_filter(self, row):
        """True if level passes filter, ie. if row should be kept"""
        likely_oncogenic_sort_order = self.oncokb_sort_order(oncokb.LIKELY_ONCOGENIC)
        return self.oncokb_sort_order(row.get(sic.ONCOKB)) <= likely_oncogenic_sort_order
  
    def oncokb_sort_order(self, level):
        oncokb_levels = [self.reformat_level_string(level) for level in oncokb.ORDERED_LEVELS]
        order = None
        i = 0
        for output_level in oncokb_levels:
            if level == output_level:
                order = i
                break
            i+=1
        if order == None:
            #self.logger.warning(
            #    "Unknown OncoKB level '{0}'; known levels are {1}".format(level, self.oncokb_levels)
            #)
            order = len(oncokb_levels)+1 # unknown levels go last
        return order

    def parse_oncokb_level(self, row_dict):
        # find oncokb level string: eg. "Level 1", "Likely Oncogenic", "None"
        max_level = None
        for level in oncokb.THERAPY_LEVELS:
            if not self.is_null_string(row_dict[level]):
                max_level = level
                break
        if max_level:
            parsed_level = self.reformat_level_string(max_level)
        elif not self.is_null_string(row_dict[sic.ONCOGENIC]):
            parsed_level = row_dict[sic.ONCOGENIC]
        else:
            parsed_level = sic.NA
        return parsed_level

    def read_cytoband_map(self):
        input_path = self.cytoband_path
        cytobands = {}
        with open(input_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                cytobands[row[sic.HUGO_SYMBOL_TITLE_CASE]] = row['Chromosome']
        return cytobands

    def read_mutation_copy_states(self):
        # convert copy state to human readable string; return mapping of gene -> copy state
        copy_state_conversion = {
            0: "Neutral",
            1: "Gain",
            2: "Amplification",
            -1: "Shallow Deletion",
            -2: "Deep Deletion"
        }
        copy_states = {}
        with open(os.path.join(self.work_dir, sic.CNA_SIMPLE)) as in_file:
            first = True
            for row in csv.reader(in_file, delimiter="\t"):
                if first:
                    first = False
                else:
                    [gene, category] = [row[0], int(row[1])]
                    copy_states[gene] = copy_state_conversion.get(category, sic.UNKNOWN)
        return copy_states

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
        rows = sorted(rows, key=lambda row: self.oncokb_sort_order(row[sic.ONCOKB]))
        return rows
