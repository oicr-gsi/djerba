"""
List of functions to convert MSI information into json format.
"""

# IMPORTS
import base64
import csv
import json
import logging
import os
import pandas as pd
import djerba.plugins.msi.constants as constants
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
from djerba.util.subprocess_runner import subprocess_runner


class data_builder:
  
  MSS_CUTOFF = 5.0
  MSI_CUTOFF = 15.0
  MSI_FILE = 'msi.txt'
  
  GENOMIC_BIOMARKERS = 'genomic_biomarkers.maf'
  
  MUTATIONS_EXTENDED = 'data_mutations_extended.txt'
  VARIANT_CLASSIFICATION = 'Variant_Classification'
  
  V7_TARGET_SIZE = 37.285536 # inherited from CGI-Tools
  
  DATA_SEGMENTS = 'data_segments.txt'
  MINIMUM_MAGNITUDE_SEG_MEAN = 0.2
  GENOME_SIZE = 3*10**9 # TODO use more accurate value when we release a new report format
  
  input_dir = "../plugins/msi/test/"
  r_script_dir = "../R_plots/"
  log_level = logging.WARNING
  log_path = None

  
  # --------------------- INITIALIZER --------------------
  
  def __init__(self, input_dir, log_level=logging.WARNING, log_path=None):
      self.log_level = log_level
      self.log_path = log_path
  #  self.data_dir = os.path.join(os.environ['DJERBA_BASE_DIR'], constants.DATA_DIR_NAME)
  #  self.r_script_dir = os.path.join(os.environ['DJERBA_BASE_DIR'], 'R_plots')  

  
  i#def build_MSI_only(self, input_dir, sample_ID):
   #   rows = []
   #   genomic_biomarkers_path = input_dir
   #   with open(genomic_biomarkers_path, "w") as genomic_biomarkers_file:
   #       rows.append(self.call_MSI(sample_ID, genomic_biomarkers_file))
#
#      data = {
#          constants.CLINICALLY_RELEVANT_VARIANTS: len(rows),
#          constants.BODY: rows
#          }
#      return data


  def call_MSI(self, msi_value):
      """convert MSI percentage into a Low, Inconclusive or High call"""
      msi_dict = {constants.ALT: constants.MSI,
                  constants.ALT_URL: "https://www.oncokb.org/gene/Other%20Biomarkers/MSI-H",
                  constants.METRIC_VALUE: msi_value
                  }
      if msi_value >= self.MSI_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = True
          msi_dict[constants.METRIC_ALTERATION] = "MSI-H"
          msi_dict[constants.METRIC_TEXT] = "Microsatellite Instability High (MSI-H)"
      elif msi_value < self.MSI_CUTOFF and msi_value >= self.MSS_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = False
          msi_dict[constants.METRIC_ALTERATION] = "INCONCLUSIVE"
          msi_dict[constants.METRIC_TEXT] = "Inconclusive Microsatellite Instability status"
      elif msi_value < self.MSS_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = False
          msi_dict[constants.METRIC_ALTERATION] = "MSS"
          msi_dict[constants.METRIC_TEXT] = "Microsatellite Stable (MSS)"
      else:
          msg = "MSI value extracted from file is not a number"
          self.logger.error(msg)
          raise RuntimeError(msg)
      return(msi_dict)

  def extract_MSI(self, msi_file_path = None):
      if msi_file_path == None:
          msi_file_path = os.path.join(self.input_dir, self.MSI_FILE_NAME)
      with open(msi_file_path, 'r') as msi_file:
          reader_file = csv.reader(msi_file, delimiter="\t")
          for row in reader_file:
              try: 
                  msi_value = float(row[2])
              except IndexError as err:
                  msg = "Incorrect number of columns in msisensor row: '{0}'".format(row)+\
                        "read from '{0}'".format(os.path.join(self.input_dir, self.MSI_FILE_NAME))
                  self.logger.error(msg)
                  raise RuntimeError(msg) from err
      return msi_value
  
  def write_biomarker_plot(self, out_dir,marker):
      out_path = os.path.join(out_dir, marker+'.svg')
      args = [
          os.path.join(self.r_script_dir, 'biomarkers_plot.R'),
          '-d', self.input_dir
      ]
      subprocess_runner(self.log_level, self.log_path).run(args)
      self.logger.info("Wrote biomarkers plot to {0}".format(out_path))
      return out_path
