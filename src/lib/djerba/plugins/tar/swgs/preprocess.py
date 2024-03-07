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
from djerba.util.environment import directory_finder
from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.oncokb.annotator import oncokb_annotator
from shutil import copyfile
import djerba.plugins.tar.swgs.constants as constants 

class preprocess(logger):

  def __init__(self, tumour_id, oncotree_code, work_dir, log_level=logging.DEBUG, log_path=None):

    finder = directory_finder(log_level, log_path)
    # CONSTANTS
    self.GENECODE_PATH = os.path.join(finder.get_data_dir(), 'gencode_v33_hg38_genes.bed')
    self.ONCOLIST_PATH = "/20200818-oncoKBcancerGeneList.tsv"

    # DIRECTORIES
    self.logger = self.get_logger(log_level, __name__, log_path)
    self.work_dir = work_dir
    self.tmp_dir = os.path.join(self.work_dir, 'tmp')
    if os.path.isdir(self.tmp_dir):
        self.logger.debug("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
    elif os.path.exists(self.tmp_dir):
        msg = "tmp dir path {0} exists but is not a directory".format(self.tmp_dir)
        self.logger.error(msg)
        raise RuntimeError(msg)
    else:
        self.logger.debug("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
        os.mkdir(self.tmp_dir)
    self.r_script_dir = finder.get_base_dir() + "/plugins/tar/swgs/Rscripts"
    self.data_dir = finder.get_data_dir()
    self.tumour_id = tumour_id
    self.oncotree_code = oncotree_code
    
    # For oncokb annotator 
    self.cache_params = None

  # ----------------------- to do all the pre-processing --------------------
    
    
  def run_R_code(self, seg_path):
    
    cmd = [
        'Rscript', self.r_script_dir + "/process_data.r",
        '--basedir', self.r_script_dir,
        '--outdir', self.work_dir,
        '--segfile', seg_path,
        '--genebed', self.GENECODE_PATH,
        '--oncolist', self.data_dir + self.ONCOLIST_PATH
    ]

    runner = subprocess_runner()
    result = runner.run(cmd, "main R script")
    self.postprocess()
    return result

 
  def preprocess_seg(self, seg_file):
    """
    Filter for amplifications.
    """
    seg_path =  os.path.join(seg_file)
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
    
    if not df_seg.empty:
        return out_path
    else:
        return None

  def postprocess(self):
     """
    Annotate CNA data
     """
     annotator = oncokb_annotator(
            self.tumour_id,
            self.oncotree_code,
            self.work_dir,
            self.tmp_dir,
            self.cache_params,
     )
     annotator.annotate_cna()
