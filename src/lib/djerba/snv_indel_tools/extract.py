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
import djerba.snv_indel_tools.constants as constants
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
import djerba.extract.oncokb.constants as oncokb
from djerba.util.subprocess_runner import subprocess_runner

class data_builder:


  ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
  data_dir = os.environ.get('DJERBA_BASE_DIR') + '/data/' 
  ALTERATION_UPPER_CASE = 'ALTERATION'
  cytoband_path = data_dir + "cytoBand.txt"
  ONCOGENIC = 'ONCOGENIC'
  CNA_ANNOTATED = "data_CNA_oncoKBgenes_nonDiploid_annotated.txt"
  HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
  HUGO_SYMBOL_TITLE_CASE = 'Hugo_Symbol'
  NA = 'NA'
  all_reported_variants = set()
  CNA_SIMPLE = 'data_CNA.txt'
  UNKNOWN = 'Unknown'
  CNA_ARATIO = 'data_CNA_oncoKBgenes_ARatio.txt'
  MUTATIONS_EXTENDED = 'data_mutations_extended.txt'
  MUTATIONS_EXTENDED_ONCOGENIC = 'data_mutations_extended_oncogenic.txt'
  VARIANT_CLASSIFICATION = 'Variant_Classification'
  HGVSP_SHORT = 'HGVSp_Short'
  HGVSC = 'HGVSc'
  ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
  is_wgts = True
  EXPR_PCT_TCGA = 'data_expression_percentile_tcga.txt'
  oncotree_uc = 'PAAD'
  TUMOUR_VAF = 'tumour_vaf'
  if is_wgts == True:
      expr_input = EXPR_PCT_TCGA
  else:
      expr_input = None

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
  

  def __init__(self, work_dir, tar):
    self.work_dir = work_dir
    self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/snv_indel_tools/Rscripts"
    self.tar = tar


  def build_small_mutations_and_indels(self):
    # read in small mutations; output rows for oncogenic mutations
    #self.logger.debug("Building data for small mutations and indels table")
    rows = []
    mutation_copy_states = self.read_mutation_copy_states()
    if self.tar == True:
        LOH_state = None
    else:
        mutation_LOH_states = self.read_mutation_LOH()
    if self.is_wgts == True and self.tar == False:
        mutation_expression = self.read_expression()
        has_expression_data = True
    else:
        mutation_expression = {}
        has_expression_data = False
    with open(os.path.join(self.work_dir, self.MUTATIONS_EXTENDED_ONCOGENIC)) as data_file:
        for input_row in csv.DictReader(data_file, delimiter="\t"):
            gene = input_row[self.HUGO_SYMBOL_TITLE_CASE]
            cytoband = self.get_cytoband(gene)
            protein = input_row[self.HGVSP_SHORT]
            if self.tar == False:
                LOH_state = mutation_LOH_states[gene]
            if 'splice' in input_row[self.VARIANT_CLASSIFICATION].lower():
                protein = 'p.? (' + input_row[self.HGVSC] + ')'  
            row = {
                constants.GENE: gene,
                constants.GENE_URL: self.build_gene_url(gene),
                constants.CHROMOSOME: cytoband,
                constants.PROTEIN: protein,
                constants.PROTEIN_URL: self.build_alteration_url(gene, protein, self.oncotree_uc),
                constants.MUTATION_TYPE: re.sub('_', ' ', input_row[self.VARIANT_CLASSIFICATION]),
                constants.EXPRESSION_METRIC: mutation_expression.get(gene), # None for WGS assay
                constants.VAF_PERCENT: int(round(float(input_row[self.TUMOUR_VAF]), 2)*100),
                constants.TUMOUR_DEPTH: int(input_row[constants.TUMOUR_DEPTH]),
                constants.TUMOUR_ALT_COUNT: int(input_row[constants.TUMOUR_ALT_COUNT]),
                constants.COPY_STATE: mutation_copy_states.get(gene, self.UNKNOWN),
                constants.LOH_STATE: LOH_state,
                constants.ONCOKB: self.parse_oncokb_level(input_row)
            }
            rows.append(row)
    #self.logger.debug("Sorting and filtering small mutation and indel rows")
    rows = list(filter(self.oncokb_filter, self.sort_variant_rows(rows)))
    for row in rows: self.all_reported_variants.add((row.get(constants.GENE), row.get(constants.CHROMOSOME)))
    data = {
        constants.HAS_EXPRESSION_DATA: has_expression_data,
        constants.VAF_PLOT: self.write_vaf_plot(self.work_dir),
        constants.CLINICALLY_RELEVANT_VARIANTS: len(rows),
        constants.TOTAL_VARIANTS: self.read_somatic_mutation_totals(),
        constants.BODY: rows
    }
    return data
    
    
    #----- necessary functions --------
    
  def write_vaf_plot(self, out_dir):
    out_path = os.path.join(out_dir, 'vaf.svg')
    args = [
        os.path.join(self.r_script_dir, 'vaf_plot.r'),
        '-d', self.work_dir,
        '-o', out_path
    ]
    subprocess_runner().run(args)
    #self.logger.info("Wrote VAF plot to {0}".format(out_path))
    return out_path

  def build_alteration_url(self, gene, alteration, cancer_code):
        #self.logger.debug('Constructing alteration URL from inputs: {0}'.format([self.ONCOKB_URL_BASE, gene, alteration, cancer_code]))
    return '/'.join([self.ONCOKB_URL_BASE, gene, alteration, cancer_code])

  def read_somatic_mutation_totals(self):
    # Count the somatic mutations
    # Splice_Region is *excluded* for TMB, *included* in our mutation tables and counts
    # Splice_Region mutations are of interest to us, but excluded from the standard TMB definition
    # The TMB mutation count is (independently) implemented and used in vaf_plot.R
    # See JIRA ticket GCGI-496
    total = 0
    with open(os.path.join(self.work_dir, self.MUTATIONS_EXTENDED)) as data_file:
        for row in csv.DictReader(data_file, delimiter="\t"):
            total += 1
    return total


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
    with open(os.path.join(self.work_dir, self.CNA_SIMPLE)) as in_file:
        first = True
        for row in csv.reader(in_file, delimiter="\t"):
            if first:
                first = False
            else:
                [gene, category] = [row[0], int(row[1])]
                copy_states[gene] = copy_state_conversion.get(category, self.UNKNOWN)
    return copy_states
      
      
  def read_mutation_LOH(self):
    # convert A-allele ratio to LOH; return mapping of gene -> LOH
    loh_states = {}
    with open(os.path.join(self.work_dir, self.CNA_ARATIO)) as in_file:
        first = True
        for row in csv.reader(in_file, delimiter="\t"):
            if first:
                first = False
            else:
                [gene, aratio] = [row[0], float(row[1])]
                if(aratio == 0.0):
                    lohcall = "Yes"
                else:
                    lohcall = "No"   
                loh_states[gene] = (lohcall+' ('+str(round(aratio,1))+')')
    return loh_states

  
  def get_cytoband(self, gene_name):
    cytoband_map = self.read_cytoband_map()
    cytoband = cytoband_map.get(gene_name)
    if not cytoband:
        cytoband = 'Unknown'
        msg = "Cytoband for gene '{0}' not found in {1}".format(gene_name, self.cytoband_path)
        #self.logger.info(msg)
    return cytoband
  
  def read_cytoband_map(self):
    input_path = self.cytoband_path
    cytobands = {}
    with open(input_path) as input_file:
        reader = csv.DictReader(input_file, delimiter="\t")
        for row in reader:
            cytobands[row[self.HUGO_SYMBOL_TITLE_CASE]] = row['Chromosome']
    return cytobands


  def read_expression(self):
    # read the expression metric (may be zscore or percentage, depending on choice of input file)
    input_path = os.path.join(self.work_dir, self.expr_input)
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
                  #self.logger.warning(msg)
                  metric = 0.0
              expr[gene] = metric
    return expr


  
  def build_gene_url(self, gene):
    return '/'.join([self.ONCOKB_URL_BASE, gene])

  
  def parse_oncokb_level(self, row_dict):
    # find oncokb level string: eg. "Level 1", "Likely Oncogenic", "None"
    max_level = None
    for level in oncokb.THERAPY_LEVELS:
        if not self.is_null_string(row_dict[level]):
            max_level = level
            break
    if max_level:
        parsed_level = self.reformat_level_string(max_level)
    elif not self.is_null_string(row_dict[self.ONCOGENIC]):
        parsed_level = row_dict[self.ONCOGENIC]
    else:
        parsed_level = self.NA
    return parsed_level

  def is_null_string(self, value):
    if isinstance(value, str):
        return value in ['', self.NA]
    else:
        msg = "Invalid argument to is_null_string(): '{0}' of type '{1}'".format(value, type(value))
        #self.logger.error(msg)
        raise RuntimeError(msg)
        
  def reformat_level_string(self, level):
    return re.sub('LEVEL_', 'Level ', level)
  
  def oncokb_filter(self, row):
    """True if level passes filter, ie. if row should be kept"""
    likely_oncogenic_sort_order = self.oncokb_sort_order(oncokb.LIKELY_ONCOGENIC)
    return self.oncokb_sort_order(row.get(constants.ONCOKB)) <= likely_oncogenic_sort_order
  
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
        order = len(self.oncokb_levels)+1 # unknown levels go last
    return order

  def sort_variant_rows(self, rows):
    # sort rows oncokb level, then by cytoband, then by gene name
    #self.logger.debug("Sorting rows by gene name")
    rows = sorted(rows, key=lambda row: row[constants.GENE])
    #self.logger.debug("Sorting rows by cytoband")
    rows = sorted(rows, key=lambda row: self.cytoband_sort_order(row[constants.CHROMOSOME]))
    #self.logger.debug("Sorting rows by oncokb level")
    rows = sorted(rows, key=lambda row: self.oncokb_sort_order(row[constants.ONCOKB]))
    return rows

  def cytoband_sort_order(self, cb_input):
    """Cytobands are (usually) of the form [integer][p or q][decimal]; also deal with edge cases"""
    end = (999, 'z', 999999)
    if cb_input in self.UNCLASSIFIED_CYTOBANDS:
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
