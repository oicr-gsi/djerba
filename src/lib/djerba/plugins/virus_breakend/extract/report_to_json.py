"""
List of functions to convert VIRUSBreakend information into json format.
"""

# IMPORTS
import base64
import csv
import json
import logging
import os
import pandas as pd
import djerba.plugins.virus_breakend.constants as constants
from djerba.util.logger import logger


class data_builder:
  
  # Excel table headers
  GENUS = 'name_genus'
  SPECIES = 'name_assigned'
  COVERAGE = 'coverage'
  LENGTH = 'endpos'
  MEANDEPTH = 'meandepth'
  INTEGRATION = 'integrations'
  
  def build_virusbreakend(self):
    """
    Reads in VIRUSBreakend file, outputs data as dictionary for json.
    """
    
    self.logger.debug("Building data for VIRUSBreakend table")
    virusbreakend_path = self.config[ini.DISCOVERED][ini.VIRUSBREAKEND_FILE] # <-------- UNSURE WHAT THIS IS SUPPOSED TO BE
    rows = []
    with open(os.path.join(self.input_dir, virusbreakend_path)) as data_file:
        for input_row in csv.DictReader(data_file, delimiter="\t"):
            row = {
                constants.GENUS: input_row[self.GENUS],
                constants.SPECIES: input_row[self.SPECIES],
                constants.COVERAGE: input_row[self.COVERAGE],
                constants.LENGTH: input_row[self.LENGTH],
                constants.MEANDEPTH: input_row[self.MEANDEPTH],
                constants.INTEGRATION: input_row[self.INTEGRATION]
            }
            rows.append(row)
            
    self.logger.debug("Sorting and filtering VIRUSBreakend rows")
    num_viruses = len(rows)
    data = {
        constants.TOTAL_VARIANTS: num_viruses
        constants.BODY: rows
    }
    return data 
