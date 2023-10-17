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

  
  def build_MSI_only(self, input_dir, sample_ID):
      rows = []
      genomic_biomarkers_path = input_dir
      with open(genomic_biomarkers_path, "w") as genomic_biomarkers_file:
          rows.append(self.call_MSI(sample_ID, genomic_biomarkers_file))

      data = {
          constants.CLINICALLY_RELEVANT_VARIANTS: len(rows),
          constants.BODY: rows
          }
      return data
  
  def call_MSI(self,sample_ID,genomic_biomarkers_file):
      #convert MSI number into Low, inconclusive or High call
      msi = self.extract_msi()
      if msi >= self.MSI_CUTOFF:
          metric_call = "MSI-H"
          metric_text = "Microsatellite Instability High (MSI-H)"
          print("Other Biomarkers\t"+sample_ID+"\tMSI-H", file=genomic_biomarkers_file)
      elif msi < self.MSI_CUTOFF and msi >= self.MSS_CUTOFF:
          metric_call = "INCONCLUSIVE"
          metric_text = "Inconclusive Microsatellite Instability status"
      elif msi < self.MSS_CUTOFF:
          metric_call = "MSS"
          metric_text = "Microsatellite Stable (MSS)"
      else:
          msg = "MSI not a number"
          self.logger.error(msg)
          raise RuntimeError(msg)
      msi_plot_location = self.write_biomarker_plot(self.input_dir,"msi")
      msi_plot_base64 = converter().convert_svg(msi_plot_location, 'MSI plot')
      row = {
          constants.ALT: constants.MSI,
          constants.METRIC_VALUE: msi,
          constants.METRIC_CALL: metric_call,
          constants.METRIC_TEXT: metric_text,
          constants.ALT_URL: "https://www.oncokb.org/gene/Other%20Biomarkers/MSI-H",
          constants.METRIC_PLOT: msi_plot_base64
      }
      return(row)
    
  def extract_msi(self):
    MSI = 0.0
    with open(os.path.join(self.input_dir, self.MSI_FILE), 'r') as msi_file:
        reader_file = csv.reader(msi_file, delimiter="\t")
        for row in reader_file:
            try: 
                MSI = float(row[2])
            except IndexError as err:
                msg = "Incorrect number of columns in msisensor row: '{0}'".format(row)+\
                      "read from '{0}'".format(os.path.join(self.input_dir, self.MSI_FILE))
                self.logger.error(msg)
                raise RuntimeError(msg) from err
    return MSI
  
  def write_biomarker_plot(self, out_dir,marker):
    out_path = os.path.join(out_dir, marker+'.svg')
    args = [
        os.path.join(self.r_script_dir, 'biomarkers_plot.R'),
        '-d', self.input_dir
    ]
    subprocess_runner(self.log_level, self.log_path).run(args)
    self.logger.info("Wrote biomarkers plot to {0}".format(out_path))
    return out_path
