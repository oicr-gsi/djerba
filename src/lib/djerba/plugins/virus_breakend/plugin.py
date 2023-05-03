"""
The purpose of this file is to prototype a plugin for VIRUSBreakend.
"""

# IMPORTS
import os
import re
import csv
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.virus_breakend.constants as constants
from djerba.plugins.virus_breakend.extract import data_builder 
from djerba.core.workspace import workspace
import djerba.util.provenance_index as index

class main(plugin_base):
  
    TEMPLATE_NAME = 'virus_template.html'
    VIRUS_SUFFIX = 'virusbreakend.vcf.summary.tsv$'

    def configure(self, config_section):
      config_section["whats_funnier_than_24"] = "25"
      try:
        self.provenance = self.subset_provenance()
        virusbreakend_path = self.parse_file_path(self.VIRUS_SUFFIX, self.provenance)
        self.logger.info("VIRUSBREAKEND ANALYSIS: Files pulled from Provenance")
        config_section[constants.VIRUSBREAKEND_FILE] = virusbreakend_path
        # TO DO: FIX THIS BECAUSE WILL NOT ENTER EXCEPT IF IT CAN'T FIND THE PATH, I.E. IT RETURNS AN EMPTY ARRAY AND NONE PATH
      except OSError:
        virusbreakend_path = config_section[constants.VIRUSBREAKEND_FILE]
        self.logger.info("VIRUSBREAKEND ANALYSIS: Files pulled from ini")
      return config_section
    
    
    def extract(self, config_section):
         
      data = {
          'plugin_name': 'VIRUSBreakend',
          'clinical': True,
          'failed': False,
          'merge_inputs': {},
          'results': data_builder().build_virusbreakend(virusbreakend_path)
      }
      return data

    def render(self, data):
      args = data
      html_dir = os.path.realpath(os.path.join(
          os.path.dirname(__file__),
          'html'
      ))
      report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
      mako_template = report_lookup.get_template(self.TEMPLATE_NAME)
      try:
          html = mako_template.render(**args)
      except Exception as err:
          msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
          self.logger.error(msg)
          raise
      return html    

    
    
    # -------------------- FILE PROVENANCE STUFF -----------------------
    
    def _get_most_recent_row(self, rows):
      # if input is empty, raise an error
      # otherwise, return the row with the most recent date field (last in lexical sort order)
      # rows may be an iterator; if so, convert to a list
      rows = list(rows)
      if len(rows)==0:
          msg = "Empty input to find most recent row; no rows meet filter criteria?"
          self.logger.debug(msg)
          raise MissingProvenanceError(msg)
      else:
          return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]
        
    def parse_file_path(self, file_pattern, provenance):
        # get most recent file of given workflow, metatype, file path pattern, and sample name
        # self._filter_* functions return an iterator
        iterrows = self._filter_file_path(file_pattern, rows=provenance)
        try:
            row = self._get_most_recent_row(iterrows)
            path = row[index.FILE_PATH]
        except MissingProvenanceError as err:
            msg = "No provenance records meet filter criteria: path-regex = {0}.".format(file_pattern)
            self.logger.debug(msg)
            path = None
        return path
    
    def _filter_file_path(self, pattern, rows):
        return filter(lambda x: re.search(pattern, x[index.FILE_PATH]), rows)
    
    def subset_provenance(self):
        provenance = []
        with self.workspace.open_gzip_file(constants.PROVENANCE_OUTPUT) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            for row in reader:
                if "virus" in row[index.WORKFLOW_NAME]:
                    provenance.append(row)
        return(provenance)

    
class MissingProvenanceError(Exception):
    pass
