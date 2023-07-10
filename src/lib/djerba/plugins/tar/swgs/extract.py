"""
List of functions to convert Copy Number Variation (CNV) information into json format.
"""

# IMPORTS
import base64
import csv
import json
import logging
import os
import re
import pandas as pd
import djerba.plugins.tar.swgs.constants as constants
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
import djerba.extract.oncokb.constants as oncokb
from djerba.util.subprocess_runner import subprocess_runner

class data_builder:

  ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
  ALTERATION_UPPER_CASE = 'ALTERATION'
  ONCOGENIC = 'ONCOGENIC'
  CNA_ANNOTATED = "data_CNA_oncoKBgenes_nonDiploid_annotated.txt"
  HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
  HUGO_SYMBOL_TITLE_CASE = 'Hugo_Symbol'
  NA = 'NA'
  all_reported_variants = set()

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

    # DIRECTORIES
    self.input_dir = "."
    self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/plugins/snv_indel/Rscripts/"
    self.report_dir = work_dir
    self.data_dir =  os.environ.get('DJERBA_BASE_DIR') + "/data/" 


  def build_graph(self):
    """
    Puts all the pieces together.
    """
    
    plot = converter().convert_svg(self.write_cnv_plot(self.input_dir), 'CNV plot')
    return plot
    
    
  def build_swgs(self):
    #self.logger.debug("Building data for copy number variation table")
    rows = []
    #else:
    #    mutation_expression = {}
    with open(os.path.join(self.input_dir, self.CNA_ANNOTATED)) as input_file:
        reader = csv.DictReader(input_file, delimiter="\t")
        for row in reader:
            gene = row[self.HUGO_SYMBOL_UPPER_CASE]
            cytoband = self.get_cytoband(gene)
            if row[self.ALTERATION_UPPER_CASE] == "Amplification":
              row = {
                  constants.GENE: gene,
                  constants.GENE_URL: self.build_gene_url(gene),
                  constants.ALTERATION: row[self.ALTERATION_UPPER_CASE],
                  constants.CHROMOSOME: cytoband,
                  constants.ONCOKB: self.parse_oncokb_level(row)
              }
              rows.append(row)
    unfiltered_cnv_total = len(rows)
    #self.logger.debug("Sorting and filtering CNV rows")
    rows = list(filter(self.oncokb_filter, self.sort_variant_rows(rows)))
    for row in rows: self.all_reported_variants.add((row.get(constants.GENE), row.get(constants.CHROMOSOME)))
    data = {
        constants.HAS_EXPRESSION_DATA: False,
        constants.CNV_PLOT: self.build_graph(),
        constants.TOTAL_VARIANTS: unfiltered_cnv_total,
        constants.CLINICALLY_RELEVANT_VARIANTS: len(rows),
        constants.BODY: rows
    }
    return data
    
  def write_cnv_plot(self, out_dir):
    """
    """
    processed_seg = self.process_seg_for_plotting("./changedAMPREVOLVE_0001_Pl_T_REV-01-001_Pl.seg.txt")
    out_path = os.path.join(out_dir, 'seg_CNV_plot.svg')
    args = [
        os.path.join(self.r_script_dir, 'cnv_plot.R'),
        '--segfile',  os.path.join(self.input_dir, processed_seg),
        '--segfiletype', 'sequenza',
        '-d',out_dir
    ]
    subprocess_runner().run(args)
    #self.logger.info("Wrote CNV plot to {0}".format(out_path))
    return out_path
      
  def process_seg_for_plotting(self, seg_file):
    """
    We need to change some column names and entries in the .seg.txt file to make the dataframe suitable for plotting.
    Do this using pandas, then convert to a processed .seg.txt file.
    The reason for this wrangling is to force this file to look like aratio_segments.txt from the CNV plugin
    """
    seg_path =  os.path.join(self.input_dir, seg_file)
 
    # Create a dataframe
    df_seg = pd.read_csv(seg_path, sep = '\t')

    # Change column names
    df_seg = df_seg.rename(columns = {"loc.start":"start.pos", 
                                      "loc.end":"end.pos", 
                                      "Corrected_Copy_Number":"CNt", 
                                      "chrom":"chromosome"})

    # Add "chr" to the beginning of the chromosome numbers
    df_seg["chromosome"] = "chr" + df_seg["chromosome"].astype(str)

    # Convert the dataframe back into a tab-delimited text file.
    out_path = os.path.join(self.input_dir, seg_file + '_processed.txt')
    df_seg.to_csv(out_path, sep = '\t', index=None)
    return out_path


   # --------------------------- ALL EXTRA FUNCTIONS ---------------------
  
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
