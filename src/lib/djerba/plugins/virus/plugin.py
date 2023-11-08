"""
Plugin for VIRUSBreakend.
"""

# IMPORTS
import os
import re
import csv
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
from djerba.core.workspace import workspace
import djerba.util.provenance_index as index
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.plugins.genomic_landscape.provenance_tools import parse_file_path
from djerba.plugins.genomic_landscape.provenance_tools import subset_provenance

class main(plugin_base):

  PRIORITY = 1200
  TEMPLATE_NAME = 'virus_template.html'
  VIRUS_RESULTS_SUFFIX = 'virusbreakend.vcf.summary.tsv'

  # Configure constants
  DONOR = 'donor'
  VIRUS_FILE = 'virus_file'

  # Extract constants
  GENUS = 'name_genus'
  SPECIES = 'name_assigned'
  COVERAGE = 'coverage'
  LENGTH = 'endpos'
  MEANDEPTH = 'meandepth'
  INTEGRATION = 'integrations'

  def specify_params(self):
    discovered = [
        self.DONOR,
        self.VIRUS_FILE,
    ]
    for key in discovered:
        self.add_ini_discovered(key)
    self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
    self.set_priority_defaults(self.PRIORITY)


  def configure(self, config_section):
    
    config = self.apply_defaults(config)
    wrapper = self.get_config_wrapper(config)
    
    if wrapper.my_param_is_null(constants.DONOR):
        if self.workspace.has_file(input_params_helper.INPUT_PARAMS_FILE):
            data = self.workspace.read_json(input_params_helper.INPUT_PARAMS_FILE)
            donor = data[constants.DONOR]
            wrapper.set_my_param(constants.DONOR, donor)
        else:
            msg = "Cannot find Donor; must be manually specified or "+\
                  "given in {0}".format(input_params_helper.INPUT_PARAMS_FILE)
            self.logger.error(msg)
            raise DjerbaPluginError(msg)
    
    # Get virus file
    donor = config[self.identifier][constants.DONOR]
    if wrapper.my_param_is_null(constants.VIRUS_FILE):
        wrapper.set_my_param(constants.VIRUS_FILE, self.get_file(donor, self.VIRUS_WORKFLOW, self.VIRUS_RESULTS_SUFFIX))
    
    return config
  
  def extract(self, config):

    wrapper = self.get_config_wrapper(config)
    work_dir = self.workspace.get_work_dir()
    
    data = {
        'plugin_name': 'VIRUSBreakend',
        'clinical': True,
        'failed': False,
        'merge_inputs': {},
        'results': self.build_virusbreakend(work_dir, virusbreakend_path)
    }
    return data

  def render(self, data):
    renderer = mako_renderer(self.get_module_dir())
    return renderer.render_name(self.TEMPLATE_NAME, data)  

  
  def get_file(self, donor, workflow, results_suffix):
    """
    pull data from results file
    """
    provenance = subset_provenance(self, workflow, donor)
    try:
        results_path = parse_file_path(self, results_suffix, provenance)
    except OSError as err:
        msg = "File with extension {0} not found".format(results_suffix)
        raise RuntimeError(msg) from err

  
  def build_virusbreakend(self, work_dir, virusbreakend_path):
    """
    Reads in VIRUSBreakend file, outputs data as dictionary for json.
    """
    rows = []
    #with open(virusbreakend_path) as datafile:
    with open(os.path.join(work_dir, virusbreakend_path)) as data_file:
        for input_row in csv.DictReader(data_file, delimiter="\t"):
            row = {
                self.GENUS: input_row[self.GENUS],
                self.SPECIES: input_row[self.SPECIES],
                self.COVERAGE: input_row[self.COVERAGE],
                self.LENGTH: input_row[self.LENGTH],
                self.MEANDEPTH: input_row[self.MEANDEPTH],
                self.INTEGRATION: input_row[self.INTEGRATION]
            }
            rows.append(row)
            
    num_viruses = len(rows)
    data = {
        self.TOTAL_VARIANTS: num_viruses,
        self.BODY: rows
    }
    return data 
    return results_path

  pass
