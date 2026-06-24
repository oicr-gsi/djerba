# IMPORTS
import os
import re
import csv
import gzip
import logging
from djerba.util.environment import directory_finder
from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.oncokb.annotator import oncokb_annotator
from shutil import copyfile
import djerba.plugins.tar.snv_indel.snv_indel_tools.constants as constants 
from djerba.plugins.base import plugin_base
import pandas as pd

class preprocess(logger):
 
  # headers of important MAF columns
  VARIANT_CLASSIFICATION = 'Variant_Classification'
  TUMOUR_SAMPLE_BARCODE = 'Tumor_Sample_Barcode'
  MATCHED_NORM_SAMPLE_BARCODE = 'Matched_Norm_Sample_Barcode'
  FILTER = 'FILTER'
  T_DEPTH = 't_depth'
  T_ALT_COUNT = 't_alt_count'
  GNOMAD_AF = 'gnomAD_AF'
  MAF_KEYS = [
      VARIANT_CLASSIFICATION,
      TUMOUR_SAMPLE_BARCODE,
      MATCHED_NORM_SAMPLE_BARCODE,
      FILTER,
      T_DEPTH,
      T_ALT_COUNT,
      GNOMAD_AF
  ]

  # Permitted MAF mutation types
  # `Splice_Region` is *included* here, but *excluded* from the somatic mutation count used to compute TMB in report_to_json.py
  # See also JIRA ticket GCGI-469
  MUTATION_TYPES_EXONIC = [
      "3'Flank",
      "3'UTR",
      "5'Flank",
      "5'UTR",
      "Frame_Shift_Del",
      "Frame_Shift_Ins",
      "In_Frame_Del",
      "In_Frame_Ins",
      "Missense_Mutation",
      "Nonsense_Mutation",
      "Nonstop_Mutation",
      "Silent",
      "Splice_Region",
      "Splice_Site",
      "Targeted_Region",
      "Translation_Start_Site"
  ]

  # disallowed MAF filter flags; from filter_flags.exclude in CGI-Tools
  FILTER_FLAGS_EXCLUDE = [
      'str_contraction',
      't_lod_fstar'
  ]

  # MAF filter thresholds
  MIN_VAF_TAR = 0.01
  MAX_UNMATCHED_GNOMAD_AF = 0.001


  def __init__(self, config, work_dir, assay, oncotree_code, cbio_id, tumour_id, normal_id, maf_file, log_level=logging.WARNING, log_path=None):
      
      # CONFIG
      self.config = config
      
      # LOGGING
      self.logger = self.get_logger(log_level, __name__, log_path)

      # DIRECTORIES
      self.report_dir = work_dir
      finder = directory_finder(log_level, log_path)
      self.r_script_dir = finder.get_base_dir() + "/plugins/tar/snv_indel/snv_indel_tools/Rscripts/"
      self.tmp_dir = os.path.join(self.report_dir, 'tmp')

      if os.path.isdir(self.tmp_dir):
          self.logger.debug("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
      elif os.path.exists(self.tmp_dir):
          msg = "tmp dir path {0} exists but is not a directory".format(self.tmp_dir)
          self.logger.error(msg)
          raise RuntimeError(msg)
      else:
          self.logger.debug("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
          os.mkdir(self.tmp_dir)
     
      # PARAMETERS
      self.assay = assay
      self.oncotree_code = oncotree_code
      self.cbio_id = cbio_id
      self.tumour_id = tumour_id
      self.normal_id = normal_id
      self.maf_file = maf_file

  
  def run_R_code(self):

    maf_path = self.preprocess_maf(self.maf_file)

    cmd = [
     'Rscript', self.r_script_dir + "/process_data.r",
     '--basedir', self.r_script_dir,
     '--outdir', self.report_dir,
     '--whizbam_url', 'https://whizbam.oicr.on.ca',
     '--tumourid', self.tumour_id,
     '--normalid', self.normal_id,
     '--cbiostudy', self.cbio_id,
     '--maffile', maf_path,
     '--tar', 'TRUE'
    ]
   
    runner = subprocess_runner()
    result = runner.run(cmd, "main R script")
    return result

  def preprocess_maf(self, maf_path):
    """Apply preprocessing and annotation to a MAF file; write results to tmp_dir"""
    tmp_path = os.path.join(self.tmp_dir, 'tmp_maf.tsv')
    # find the relevant indices on-the-fly from MAF column headers
    # use this instead of csv.DictReader to preserve the rows for output
    with \
        gzip.open(maf_path, 'rt', encoding=constants.TEXT_ENCODING) as in_file, \
        open(tmp_path, 'wt') as tmp_file:
        # preprocess the MAF file
        reader = csv.reader(in_file, delimiter="\t")
        writer = csv.writer(tmp_file, delimiter="\t")
        in_header = True
        total = 0
        kept = 0
        for row in reader:
            if in_header:
                if re.match('#version', row[0]):
                    # do not write the version header
                    continue
                else:
                    # write the column headers without change
                    writer.writerow(row)
                    indices = self._read_maf_indices(row)
                    in_header = False
            else:
                total += 1
                if self._maf_body_row_ok(row, indices, self.MIN_VAF_TAR):
                    # filter rows in the MAF body and update the tumour_id
                    row[indices.get(self.TUMOUR_SAMPLE_BARCODE)] = self.tumour_id
                    writer.writerow(row)
                    kept += 1
    # apply annotation to tempfile and return final output
    out_path = oncokb_annotator(
        self.tumour_id,
        self.oncotree_code,
        self.report_dir,
        self.tmp_dir
    ).annotate_maf(tmp_path)
    return out_path

  def _maf_body_row_ok(self, row, ix, vaf_cutoff):
    """
    Should a MAF row be kept for output?
    Implements logic from functions.sh -> hard_filter_maf() in CGI-Tools
    Expected to filter out >99.9% of input reads
    ix is a dictionary of column indices
    """
    ok = False
    row_t_depth = int(row[ix.get(self.T_DEPTH)])
    alt_count_raw = row[ix.get(self.T_ALT_COUNT)]
    gnomad_af_raw = row[ix.get(self.GNOMAD_AF)]
    row_t_alt_count = float(alt_count_raw) if alt_count_raw!='' else 0.0
    row_gnomad_af = float(gnomad_af_raw) if gnomad_af_raw!='' else 0.0
    is_matched = row[ix.get(self.MATCHED_NORM_SAMPLE_BARCODE)] != 'unmatched'
    filter_flags = re.split(';', row[ix.get(self.FILTER)])
    if row_t_depth >= 1 and \
        row_t_alt_count/row_t_depth >= vaf_cutoff and \
        (is_matched or row_gnomad_af < self.MAX_UNMATCHED_GNOMAD_AF) and \
        row[ix.get(self.VARIANT_CLASSIFICATION)] in self.MUTATION_TYPES_EXONIC and \
        not any([z in self.FILTER_FLAGS_EXCLUDE for z in filter_flags]):
        ok = True
    return ok

  def _read_maf_indices(self, row):
    indices = {}
    for i in range(len(row)):
        key = row[i]
        if key in self.MAF_KEYS:
            indices[key] = i
    if set(indices.keys()) != set(self.MAF_KEYS):
        msg = "Indices found in MAF header {0} ".format(indices.keys()) +\
                "do not match required keys {0}".format(self.MAF_KEYS)
        raise RuntimeError(msg)
    return indices
