"""
The purpose of this file is deal with pre-processing necessary files for the SWGS plugin.
They're in a separate file because the pre-processing is a little more complex.
AUTHOR: Aqsa Alam
"""

# IMPORTS
import os
import re
import csv
import gzip
import logging
import pandas as pd
from shutil import copyfile

from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.oncokb.annotator import oncokb_annotator
from djerba.util.image_to_base64 import converter
import djerba.util.oncokb.constants as oncokb
import djerba.plugins.wgts.cnv_purple.constants as cc 

class process_cnv(logger):

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir
        self.tmp_dir = os.path.join(self.work_dir, 'tmp')
        self.cytoband_path = os.environ.get('DJERBA_BASE_DIR') + cc.CYTOBAND
        self.oncokb_levels = [self.reformat_level_string(level) for level in oncokb.ORDERED_LEVELS]
        if os.path.isdir(self.tmp_dir):
            print("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
            self.logger.debug("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
        elif os.path.exists(self.tmp_dir):
            msg = "tmp dir path {0} exists but is not a directory".format(self.tmp_dir)
            self.logger.error(msg)
            raise RuntimeError(msg)
        else:
            print("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
            self.logger.debug("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
            os.mkdir(self.tmp_dir)
  
    def build_alteration_url(self, gene, alteration, cancer_code):
        self.logger.debug('Constructing alteration URL from inputs: {0}'.format([cc.ONCOKB_URL_BASE, gene, alteration, cancer_code]))
        return '/'.join([cc.ONCOKB_URL_BASE, gene, alteration, cancer_code])
 

    def build_copy_number_variation(self, assay, cna_annotated_path, oncotree_uc):
        cna_annotated_path = os.path.join(self.work_dir, cna_annotated_path)
        self.logger.debug("Building data for copy number variation table")
        rows = []
        if assay == "WGTS":
            mutation_expression = self.read_expression()
        else:
            mutation_expression = {}
        with open(cna_annotated_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                gene = row[cc.HUGO_SYMBOL_UPPER_CASE]
                cytoband = self.get_cytoband(gene)
                row = {
                    cc.EXPRESSION_METRIC: mutation_expression.get(gene), # None for WGS assay
                    cc.GENE: gene,
                    cc.GENE_URL: self.build_gene_url(gene),
                    cc.ALT: row[cc.ALTERATION_UPPER_CASE],
                    cc.ALT_URL: self.build_alteration_url(gene, row[cc.ALTERATION_UPPER_CASE], oncotree_uc),
                    cc.CHROMOSOME: cytoband,
                    'OncoKB level': self.parse_oncokb_level(row)
                }
                rows.append(row)
        unfiltered_cnv_total = len(rows)
        self.logger.debug("Sorting and filtering CNV rows")
        rows = list(filter(self.oncokb_filter, self.sort_variant_rows(rows)))
        data_table = {
        #    cc.HAS_EXPRESSION_DATA: self.HAS_EXPRESSION_DATA,
            cc.TOTAL_VARIANTS: unfiltered_cnv_total,
            cc.CLINICALLY_RELEVANT_VARIANTS: len(rows),
            cc.BODY: rows
        }
        return data_table
    
    def build_gene_url(self, gene):
        return '/'.join([cc.ONCOKB_URL_BASE, gene])

    def build_therapy_info(self, variants_annotated_file, oncotree_uc):
        # build the "FDA approved" and "investigational" therapies data
        # defined respectively as OncoKB levels 1/2/R1 and R2/3A/3B/4
        # OncoKB "LEVEL" columns contain treatment if there is one, 'NA' otherwise
        # Input files:
        # - One file each for CNVs
        # - Must be annotated by OncoKB script
        # - Must not be missing
        # - May consist of headers only (no data rows)
        # Output columns:
        # - the gene name, with oncoKB link (or pair of names/links, for fusions)
        # - Alteration name, eg. HGVSp_Short value, with oncoKB link
        # - Treatment
        # - OncoKB level
        tiered_rows = list()
        for tier in ('Approved', 'Investigational'):
            self.logger.debug("Building therapy info for level: {0}".format(tier))
            if tier == 'Approved':
                levels = oncokb.FDA_APPROVED_LEVELS
            elif tier == 'Investigational':
                levels = oncokb.INVESTIGATIONAL_LEVELS
            rows = []
            with open(variants_annotated_file) as data_file:
                for row in csv.DictReader(data_file, delimiter="\t"):
                    gene = row[cc.HUGO_SYMBOL_UPPER_CASE]
                    alteration = row[cc.ALTERATION_UPPER_CASE]
                    [max_level, therapies] = self.parse_max_oncokb_level_and_therapies(row, levels)
                    if max_level:
                        rows.append(self.treatment_row(gene, alteration, max_level, therapies, oncotree_uc, tier))
            rows = list(filter(self.oncokb_filter, self.sort_therapy_rows(rows)))
            if rows:
                tiered_rows.append(rows)
        if len(tiered_rows) > 0:
            return tiered_rows[0]
        else:
            return tiered_rows
        
    def convert_to_gene_and_annotate(self, seg_path, purity, tumour_id, oncotree_code):
        dir_location = os.path.dirname(__file__)
        genebedpath = os.path.join(dir_location, '../../..', cc.GENEBED)
        oncolistpath = os.path.join(dir_location, '../../..', cc.ONCOLIST)
        centromerespath = os.path.join(dir_location, '../../..', cc.CENTROMERES)
        cmd = [
            'Rscript', os.path.join(dir_location + "/R/process_CNA_data.r"),
            '--outdir', self.work_dir,
            '--segfile', seg_path,
            '--genebed', genebedpath,
            '--oncolist', oncolistpath,
            '--purity', purity,
            '--centromeres', centromerespath
        ]

        runner = subprocess_runner()
        result = runner.run(cmd, "main R script")
        annotator = oncokb_annotator(
                        tumour_id,
                        oncotree_code,
                        self.work_dir,
                        self.tmp_dir
                        #self.cache_params
                )
        annotator.annotate_cna()

        return result

    def cytoband_sort_order(self, cb_input):
        """Cytobands are (usually) of the form [integer][p or q][decimal]; also deal with edge cases"""
        end = (999, 'z', 999999)
        if cb_input in cc.UNCLASSIFIED_CYTOBANDS:
            msg = "Cytoband \"{0}\" is unclassified, moving to end of sort order".format(cb_input)
            self.logger.debug(msg)
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
                self.logger.warning(msg)
                (chromosome, arm, band) = end
        return (chromosome, arm, band)
    
    def get_cytoband(self, gene_name):
        cytoband_map = self.read_cytoband_map()
        cytoband = cytoband_map.get(gene_name)
        if not cytoband:
            cytoband = 'Unknown'
            msg = "Cytoband for gene '{0}' not found in {1}".format(gene_name, self.cytoband_path)
            self.logger.info(msg)
        return cytoband
    
    def is_null_string(self, value):
        if isinstance(value, str):
            return value in ['', cc.NA]
        else:
            msg = "Invalid argument to is_null_string(): '{0}' of type '{1}'".format(value, type(value))
            self.logger.error(msg)
            raise RuntimeError(msg)

    def oncokb_filter(self, row):
        """True if level passes filter, ie. if row should be kept"""
        likely_oncogenic_sort_order = self.oncokb_sort_order(oncokb.LIKELY_ONCOGENIC)
        return self.oncokb_sort_order(row.get('OncoKB level')) <= likely_oncogenic_sort_order


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
            self.logger.warning(
                "Unknown OncoKB level '{0}'; known levels are {1}".format(level, self.oncokb_levels)
            )
            order = len(self.oncokb_levels)+1 # unknown levels go last
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
        elif not self.is_null_string(row_dict[cc.ONCOGENIC]):
            parsed_level = row_dict[cc.ONCOGENIC]
        else:
            parsed_level = cc.NA
        return parsed_level

    def parse_max_oncokb_level_and_therapies(self, row_dict, levels):
        # find maximum level (if any) from given levels list, and associated therapies
        max_level = None
        therapies = []
        for level in levels:
            if not self.is_null_string(row_dict[level]):
                if not max_level: max_level = level
                therapies.append(row_dict[level])
        if max_level:
            max_level = self.reformat_level_string(max_level)
        # insert a space between comma and start of next word
        therapies = [re.sub(r'(?<=[,])(?=[^\s])', r' ', t) for t in therapies]
        return (max_level, '; '.join(therapies))
    
    def read_cytoband_map(self):
        input_path = self.cytoband_path
        cytobands = {}
        with open(input_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                cytobands[row[cc.HUGO_SYMBOL_TITLE_CASE]] = row['Chromosome']
        return cytobands

    def read_expression(self, input_path):
        # read the expression metric (may be zscore or percentage, depending on choice of input file)
        expr = {}
        with open(input_path) as input_file:
            for row in csv.reader(input_file, delimiter="\t"):
                if row[0]=='Hugo_Symbol':
                    continue
                gene = row[0]
                try:
                    metric = float(row[1])
                except ValueError as err:
                    msg = 'Cannot convert expression value "{0}" to float, '.format(row[1])+\
                            '; using 0 as fallback value: {0}'.format(err)
                    self.logger.warning(msg)
                    metric = 0.0
                expr[gene] = metric
        return expr

    def reformat_level_string(self, level):
        return re.sub('LEVEL_', 'Level ', level)

    def sort_therapy_rows(self, rows):
        # sort FDA/investigational therapy rows
        # extract a gene name from 'genes and urls' dictionary keys
        rows = sorted(
            rows,
            key=lambda row: sorted(list(row.get('Gene'))).pop(0)
        )
        rows = sorted(rows, key=lambda row: self.oncokb_sort_order(row['OncoKB level']))
        return rows
    
    def sort_variant_rows(self, rows):
        # sort rows oncokb level, then by cytoband, then by gene name
        self.logger.debug("Sorting rows by gene name")
        rows = sorted(rows, key=lambda row: row[cc.GENE])
        self.logger.debug("Sorting rows by cytoband")
        rows = sorted(rows, key=lambda row: self.cytoband_sort_order(row[cc.CHROMOSOME]))
        self.logger.debug("Sorting rows by oncokb level")
        rows = sorted(rows, key=lambda row: self.oncokb_sort_order(row['OncoKB level']))
        return rows

    def treatment_row(self, genes_arg, alteration, max_level, therapies, oncotree_uc, tier):
        row = {
            'Tier': tier,
            'OncoKB level': max_level,
            'Treatments': therapies,
            'Gene': genes_arg,
            'Gene_URL': self.build_gene_url(genes_arg),
            cc.ALT: alteration,
            cc.ALT_URL: self.build_alteration_url(genes_arg, alteration, oncotree_uc)
        }
        return row
    
