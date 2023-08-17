"""
The purpose of this file is deal with pre-processing necessary files for the SWGS plugin.
They're in a separate file because the pre-processing is a little more complex.
AUTHOR: Aqsa Alam
"""

# IMPORTS
import os
import csv
import gzip
import logging
import pandas as pd
from djerba.util.logger import logger
from djerba.sequenza import sequenza_reader
from djerba.util.subprocess_runner import subprocess_runner
from djerba.extract.oncokb.annotator import oncokb_annotator
from shutil import copyfile
import djerba.cnv_tools.constants as ctc 
import djerba.cnv_tools.constants as constants 
import djerba.snv_indel_tools.constants as sic

class preprocess(logger):

  def __init__(self, report_dir, log_level=logging.WARNING, log_path=None):
      self.log_level = log_level
      self.log_path = log_path
      self.logger = self.get_logger(log_level, __name__, log_path)
      self.report_dir = report_dir
      self.tmp_dir = os.path.join(self.report_dir, 'tmp')
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
  
  def preprocess_seg_sequenza(self, sequenza_path):
      """
      Extract the SEG file from the .zip archive output by Sequenza
      Apply preprocessing and write results to tmp_dir
      Replace entry in the first column with the tumour ID
      """

      seg_path = sequenza_reader(sequenza_path).extract_cn_seg_file(self.tmp_dir, self.sequenza_gamma)
      out_path = os.path.join(self.tmp_dir, 'seg.txt')
      with open(seg_path, 'rt') as seg_file, open(out_path, 'wt') as out_file:
          reader = csv.reader(seg_file, delimiter="\t")
          writer = csv.writer(out_file, delimiter="\t")
          in_header = True
          for row in reader:
              if in_header:
                  in_header = False
              else:
                  row[0] = self.tumour_id
              writer.writerow(row)
      return out_path

  def preprocess_seg_tar(self, seg_file):
    """
    Filter for amplifications.
    """
    seg_path =  os.path.join(self.seg_file)
    # Create a dataframe so we can filter by amplifications only...or in this case, by gain only for testing.
    df_seg = pd.read_csv(seg_path, sep = '\t')
    df_seg = df_seg[df_seg["call"].str.contains("AMP|HLAMP") == True]

    # Delete the seg.mean column, and rename the Corrected_Copy_Number column to seg.mean
    df_seg = df_seg.drop(columns = "seg.median.logR")
    df_seg = df_seg.rename(columns={"Corrected_Copy_Number": "seg.mean"})
    df_seg = df_seg.rename(columns={"start": "loc.start"})
    df_seg = df_seg.rename(columns={"end": "loc.end"})

    # Convert the dataframe back into a tab-delimited text file.
    out_path = os.path.join(self.work_dir, 'seg_amplifications.txt')
    df_seg.to_csv(out_path, sep = '\t', index=None)

    return out_path
  
  def run_R_code(self, seg_file, assay):
    dir_location = os.path.dirname(__file__)
    if assay = "TAR":
      seg_path = self.preprocess_seg_tar(seg_file)
    else:
      seg_path = self.preprocess_seg_sequenza(seg_file)

    cmd = [
        'Rscript', self.r_script_dir_swgs + "/process_CNA_data.r",
        '--basedir', self.r_script_dir,
        '--outdir', self.work_dir,
        '--segfile', seg_path,
        '--genebed', os.path.join(dir_location, '..', ctc.GENEBED),
        '--oncolist', os.path.join(dir_location, '..', sic.ONCOLIST)
    ]

    runner = subprocess_runner()
    result = runner.run(cmd, "main R script")
    annotator = oncokb_annotator(
                 self.tumour_id,
                 self.oncotree_code,
                 self.report_dir,
                 self.tmp_dir,
                 self.cache_params
         )
    annotator.annotate_cna()

    return result
