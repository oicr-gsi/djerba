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
import djerba.plugins.swgs.constants as constants 

class preprocess:

  # FOR TESTING
  sequenza_path = "/.mounts/labs/CGI/cap-djerba/PASS01/PANX_1550/PANX_1550_Lv_M_WG_100-PM-064_LCM3_results.zip"
  tumour_id = "100-PM-064_LCM3"
  oncotree_code = "paad"
  gamma = 500
  solution = "_primary_"
  seg_file = "./changedAMPREVOLVE_0001_Pl_T_REV-01-001_Pl.seg.txt"

  def __init__(self, work_dir, tar):

    # DIRECTORIES
    self.report_dir = work_dir
    self.tmp_dir = os.path.join(self.report_dir, 'tmp')
    if os.path.isdir(self.tmp_dir):
        print("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
        #self.logger.debug("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
    elif os.path.exists(self.tmp_dir):
        msg = "tmp dir path {0} exists but is not a directory".format(self.tmp_dir)
        #self.logger.error(msg)
        raise RuntimeError(msg)
    else:
        #print("Creating tmp dir {0} for R script wrapper".format(tmp_dir))
        #self.logger.debug("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
        os.mkdir(self.tmp_dir)
    self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/plugins/snv_indel/Rscripts"
    
    # IS IT TAR? PARAMETER
    self.tar = tar

    # RANDOM
    cache_params = None
    log_level = "logging.WARNING"
    log_path = "None"
  

  # ----------------------- to do all the pre-processing --------------------
    
    
  def run_R_code(self):
    seg_path = self.preprocess_seg(self.seg_file)

    cmd = [
        'Rscript', "../process_CNA_data.r",
        '--basedir', self.r_script_dir,
        '--outdir', self.report_dir,
        '--segfile', seg_path,
        '--genebed', "/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/gencode_v33_hg38_genes.bed",
        '--oncolist', "../../../data/20200818-oncoKBcancerGeneList.tsv"
        #'--gain', "0.0341",
        #'--ampl', "0.1009",
        #'--htzd', "-0.0358",
        #'--hmzd', "-0.1094"
    ]

    runner = subprocess_runner()
    result = runner.run(cmd, "main R script")
    self.postprocess()
    return result

  
  def preprocess_seg(self, seg_file):
    """
    Filter for amplifications.
    For now, filter for GAIN because I don't see any amplifications in the file.
    TO DO: change header names
    """
    seg_path =  os.path.join(self.report_dir, seg_file)
    
    # Create a dataframe so we can filter by amplifications only...or in this case, by gain only for testing.
    df_seg = pd.read_csv(seg_path, sep = '\t')
    df_seg = df_seg[df_seg["call"].str.contains("AMP|HLAMP") == True]
   
    # Delete the seg.mean column, and rename the Corrected_Copy_Number column to seg.mean
    df_seg = df_seg.drop(columns = "seg.mean")
    df_seg = df_seg.rename(columns={"Corrected_Copy_Number": "seg.mean"})

    # Convert the dataframe back into a tab-delimited text file.
    out_path = os.path.join(self.report_dir, 'seg_amplifications.txt')
    df_seg.to_csv(out_path, sep = '\t', index=None)

    return out_path


  def postprocess(self):
     """
    Annotate CNA data
     """
     annotator = oncokb_annotator(
            self.tumour_id,
            self.oncotree_code,
            self.report_dir,
            self.tmp_dir,
            self.cache_params,
     )
     annotator.annotate_cna()
