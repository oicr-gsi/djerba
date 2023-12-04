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
from djerba.plugins.genomic_landscape.provenance_tools import parse_file_path
from djerba.plugins.genomic_landscape.provenance_tools import subset_provenance

class main(plugin_base):

  PRIORITY = 1200
  PLUGIN_VERSION = '1.0.0'
  TEMPLATE_NAME = 'virus_template.html'

  # Configure constants
  DONOR = 'donor'
  VIRUS_FILE = 'virus_file'
  VIRUS_WORKFLOW = 'virusbreakend'

  # Extract constants
  #GENUS = 'name_genus'
  SPECIES = 'name_species'
  ASSIGNED = 'name_assigned'
  COVERAGE = 'coverage'
  LENGTH = 'endpos'
  INTEGRATION = 'integrations'
  DRIVER = 'driver'
  BODY = 'Body'
  TOTAL_VARIANTS = 'Total variants'

  # List of driver viruses
  # Driver viruses from: https://github.com/hartwigmedical/hmftools/blob/master/virus-interpreter/src/test/resources/virus_interpreter/real_virus_reporting_db.tsv
  DRIVER_VIRUSES = ["Human gammaherpesvirus 4",
                    "Hepatitis B virus",
                    "Human gammaherpesvirus 8",
                    "Alphapapillomavirus 11",
                    "Alphapapillomavirus 5",
                    "Alphapapillomavirus 6",
                    "Alphapapillomavirus 7",
                    "Alphapapillomavirus 9",
                    "Alphapapillomavirus 1",
                    "Alphapapillomavirus 10",
                    "Alphapapillomavirus 13",
                    "Alphapapillomavirus 3",
                    "Alphapapillomavirus 8",
                    "Human polyomavirus 5"]

  def specify_params(self):
    discovered = [
        self.DONOR,
        self.VIRUS_FILE,
    ]
    for key in discovered:
        self.add_ini_discovered(key)
    self.set_ini_default(core_constants.ATTRIBUTES, 'research')
    self.set_priority_defaults(self.PRIORITY)


  def configure(self, config):
    
    config = self.apply_defaults(config)
    wrapper = self.get_config_wrapper(config)
    
    # Get parameters
    wrapper = self.update_wrapper_if_null(
        wrapper,
        input_params_helper.INPUT_PARAMS_FILE,
        self.DONOR,
        input_params_helper.DONOR
    )

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
    #with open(virusbreakend_path) as datafile:
    with open(os.path.join(work_dir, virus_path)) as data_file:
        for input_row in csv.DictReader(data_file, delimiter="\t"):
            row = {
                #self.GENUS: input_row[self.GENUS],
                self.SPECIES: input_row[self.SPECIES],
                self.ASSIGNED: input_row[self.ASSIGNED],
                self.COVERAGE: input_row[self.COVERAGE],
                self.LENGTH: input_row[self.LENGTH],
                self.INTEGRATION: input_row[self.INTEGRATION]
            }
            
            # Check if it's a driver virus
            if input_row[self.SPECIES] in self.DRIVER_VIRUSES:
                row[self.DRIVER] = "Yes"
            else:
                row[self.DRIVER] = "No"

            rows.append(row)
          
    num_viruses = len(rows)
    data = {
        self.TOTAL_VARIANTS: num_viruses,
        self.BODY: rows
    }
    return data 
    return results_path

  pass
