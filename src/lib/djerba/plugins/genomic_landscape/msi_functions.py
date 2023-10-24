"""
List of functions to convert MSI information into json format.
"""

# IMPORTS
import base64
import csv
import logging
import os
import numpy
import djerba.plugins.genomic_landscape.constants as constants
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
from djerba.util.subprocess_runner import subprocess_runner

def run(self, work_dir, msi_file, biomarkers_path, tumour_id):
      """
      Runs all functions below.
      Assembles a chunk of json.
      """
      msi_summary = preprocess_msi(work_dir, msi_file)
      msi_data = assemble_MSI(self, work_dir, msi_summary)
      
      # Write to genomic biomarkers maf if MSI is actionable
      if msi_data[constants.METRIC_ACTIONABLE]:
          with open(biomarkers_path, "a") as biomarkers_file:
              row = '\t'.join([constants.HUGO_SYMBOL, tumour_id, msi_data[constants.METRIC_ALTERATION]])
              biomarkers_file.write(row + "\n")
      
      return msi_data

def preprocess_msi(work_dir, msi_file):
      """
      summarize msisensor file
      """
      out_path = os.path.join(work_dir, 'msi.txt')
      msi_boots = []
      with open(msi_file, 'r') as msi_file:
          reader_file = csv.reader(msi_file, delimiter="\t")
          for row in reader_file:
              msi_boots.append(float(row[3]))
      msi_perc = numpy.percentile(numpy.array(msi_boots), [0, 25, 50, 75, 100])
      with open(out_path, 'w') as out_file:
          print("\t".join([str(item) for item in list(msi_perc)]), file=out_file)
      return out_path

def assemble_MSI(self, work_dir, msi_summary):
      msi_value = extract_MSI(self, work_dir, msi_summary)
      msi_dict = call_MSI(self, msi_value)
      msi_plot_location = write_biomarker_plot(self,work_dir, "msi")
      msi_dict[constants.METRIC_PLOT] = converter().convert_svg(msi_plot_location, 'MSI plot')
      return(msi_dict)

def call_MSI(self, msi_value):
      """convert MSI percentage into a Low, Inconclusive or High call"""
      msi_dict = {constants.ALT: constants.MSI,
                  constants.ALT_URL: "https://www.oncokb.org/gene/Other%20Biomarkers/MSI-H",
                  constants.METRIC_VALUE: msi_value
                  }
      if msi_value >= constants.MSI_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = True
          msi_dict[constants.METRIC_ALTERATION] = "MSI-H"
          msi_dict[constants.METRIC_TEXT] = "Microsatellite Instability High (MSI-H)"
      elif msi_value < constants.MSI_CUTOFF and msi_value >= constants.MSS_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = False
          msi_dict[constants.METRIC_ALTERATION] = "INCONCLUSIVE"
          msi_dict[constants.METRIC_TEXT] = "Inconclusive Microsatellite Instability status"
      elif msi_value < constants.MSS_CUTOFF:
          msi_dict[constants.METRIC_ACTIONABLE] = False
          msi_dict[constants.METRIC_ALTERATION] = "MSS"
          msi_dict[constants.METRIC_TEXT] = "Microsatellite Stable (MSS)"
      else:
          msg = "MSI value extracted from file is not a number"
          self.logger.error(msg)
          raise RuntimeError(msg)
      return(msi_dict)

def extract_MSI(self, work_dir, msi_file):
      if msi_file == None:
          msi_file = os.path.join(work_dir, constants.MSI_FILE_NAME)
      with open(msi_file, 'r') as msi_file:
          reader_file = csv.reader(msi_file, delimiter="\t")
          for row in reader_file:
              try:
                  msi_value = float(row[2])
              except IndexError as err:
                  msg = "Incorrect number of columns in msisensor row: '{0}'".format(row)+\
                        "read from '{0}'".format(os.path.join(work_dir, constants.MSI_FILE_NAME))
                  self.logger.error(msg)
                  raise RuntimeError(msg) from err
      return msi_value

def write_biomarker_plot(self, work_dir, marker):
      out_path = os.path.join(work_dir, marker+'.svg')
      args = [
          os.path.join(self.r_script_dir, 'msi_plot.R'),
          '-d', work_dir
      ]
      subprocess_runner(self.log_level, self.log_path).run(args)
      self.logger.info("Wrote msi plot to {0}".format(out_path))
      return out_path
