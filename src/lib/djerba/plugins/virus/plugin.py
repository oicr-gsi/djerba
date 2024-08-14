"""
Plugin for VIRUSBreakend.
"""

import os
import re
import csv
from djerba.plugins.base import plugin_base, DjerbaPluginError
from mako.lookup import TemplateLookup
from djerba.util.render_mako import mako_renderer
from djerba.core.workspace import workspace
import djerba.util.provenance_index as index
import djerba.core.constants as core_constants
from djerba.helpers.input_params_helper.helper import main as input_params_helper
import djerba.core.constants as core_constants

class main(plugin_base):

  PRIORITY = 300
  PLUGIN_VERSION = '1.0.0'
  TEMPLATE_NAME = 'virus_template.html'

  # Configure constants
  DONOR = 'donor'
  VIRUS_FILE = 'virus_file'
  VIRUS_WORKFLOW = 'virusbreakend'

  # Extract constants
  SPECIES = 'name_species'
  ASSIGNED = 'name_assigned'
  NAME = 'common_name'
  COVERAGE = 'coverage'
  LENGTH = 'endpos'
  INTEGRATION = 'integrations'
  QC = 'QCStatus'
  BODY = 'Body'
  TOTAL_VARIANTS = 'Total variants'

  # List of driver viruses
  # Driver viruses from: https://github.com/hartwigmedical/hmftools/blob/master/virus-interpreter/src/test/resources/virus_interpreter/real_virus_reporting_db.tsv

  DRIVER_VIRUSES = {"Human gammaherpesvirus 4": "EBV",
                    "Hepatitis B virus": "HBV",
                    "Human gammaherpesvirus 8": "HHV-8",
                    "Alphapapillomavirus 11": "HPV",
                    "Alphapapillomavirus 5": "HPV",
                    "Alphapapillomavirus 6": "HPV",
                    "Alphapapillomavirus 7": "HPV",
                    "Alphapapillomavirus 9": "HPV",
                    "Alphapapillomavirus 1": "HPV",
                    "Alphapapillomavirus 10": "HPV",
                    "Alphapapillomavirus 13": "HPV",
                    "Alphapapillomavirus 3": "HPV",
                    "Alphapapillomavirus 8": "HPV",
                    "Human polyomavirus 5": "MCV"}
  
  # List of QC statuses to exclude
  FAIL_QC = ['FAIL_CONTAMINATION',
             'FAIL_NO_TUMOR',
             'LOW_VIRAL_COVERAGE']

  def specify_params(self):
    self.add_ini_discovered(self.VIRUS_FILE)
    self.set_ini_default(core_constants.ATTRIBUTES, 'research')
    self.set_priority_defaults(self.PRIORITY)


  def configure(self, config):
    
    config = self.apply_defaults(config)
    wrapper = self.get_config_wrapper(config)

     # Get virus file from path_info.json
    wrapper = self.update_wrapper_if_null(
        wrapper,
        core_constants.DEFAULT_PATH_INFO,
        self.VIRUS_FILE,
        self.VIRUS_WORKFLOW
    )
    return config
  
  def extract(self, config):

    wrapper = self.get_config_wrapper(config)
    work_dir = self.workspace.get_work_dir()
    virus_path = config[self.identifier][self.VIRUS_FILE]

    data = {
        'plugin_name': 'VIRUSBreakend',
        'version': self.PLUGIN_VERSION,
        'priorities': wrapper.get_my_priorities(),
        'attributes': wrapper.get_my_attributes(),
        'merge_inputs': {},
        'results': self.build_virus(work_dir, virus_path)
    }
    return data

  def render(self, data):
    renderer = mako_renderer(self.get_module_dir())
    return renderer.render_name(self.TEMPLATE_NAME, data)  

  def build_virus(self, work_dir, virus_path):
    """
    Reads in VIRUSBreakend file, outputs data as dictionary for json.
    """
    rows = []
    with open(os.path.join(work_dir, virus_path)) as data_file:
        for input_row in csv.DictReader(data_file, delimiter="\t"):
            
            # To be oncogenic, it has to be one of the driver viruses and have more than 0 breakpoints and not fail QC
            if float(input_row[self.INTEGRATION]) > 0 and input_row[self.SPECIES] in self.DRIVER_VIRUSES and input_row[self.QC] not in self.FAIL_QC:
                row = {
                    self.ASSIGNED: input_row[self.ASSIGNED],
                    self.NAME: self.DRIVER_VIRUSES[input_row[self.SPECIES]],
                    self.COVERAGE: input_row[self.COVERAGE],
                    self.LENGTH: input_row[self.LENGTH],
                    self.INTEGRATION: input_row[self.INTEGRATION]
                }
            
                # Additional check for Human gammaherpesvirus 4 (Epstein-Barr virus)
                # Coverage for this must be above 90%
                if input_row[self.SPECIES] == 'Human gammaherpesvirus 4' and not(int(input_row[self.COVERAGE]) >= 90):
                    continue

                rows.append(row)

         
    num_viruses = len(rows)
    data = {
        self.TOTAL_VARIANTS: num_viruses,
        self.BODY: rows
    }
    return data 
    return results_path
