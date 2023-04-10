"""
This script describes a list of functions to render the VIRUSBreakend data from the json into HTML.
"""

# IMPORTS
import re
from markdown import markdown
from time import strftime
from string import Template
import djerba.plugins.virus_breakend.constants as constants

class html_builder:
  
  # ------------------- TABLE FORMAT FUNCTIONS -------------------
  
  def section_cells_begin(self, section_title, main_or_supp):
    """
    Describes how the section cells begin.
    Taken from the original json_to_html.py from the non-plugin Djerba.
    
    Begin a cell structure with title in left-hand cell, body in right-hand cell
    """
    permitted = ['main', 'supp']
    if main_or_supp not in permitted:
        msg = "Section type argument '{0}' not in {1}".format(main_or_supp, permitted)
        self.logger.error(msg)
        raise RuntimeError(msg)
    template = '<hr class="big-white-line" ><div class="twocell{0}"><div class="oneoftwocell{0}">{1}</div><div class="twooftwocell{0}" ><hr class="big-line" >'
    cell = template.format(main_or_supp,section_title)
    return cell
  
  def section_cells_end(self):
    """
    Describes how the section cells end.
    Taken from the original json_to_html.py from the non-plugin Djerba.
    
    Closes <div class="twocell... and <div class="twooftwocell...
    """
    return "</div></div>\n"
  
  
  # ----------------------- VIRUS FUNCTIONS ----------------------
  
  def virusbreakend_header(self):
    """
    Creates the header for the VIRUSBreakend table.
    """
    names = [
        constants.GENUS,
        constants.SPECIES,
        constants.CONVERAGE,
        constants.LENGTH,
        constants.MEANDEPTH,
        constants.INTEGRATION
    ]
    return self.table_header(names)

      
    def virusbreakend_rows(self, mutation_info):
      """
      Creates the rows for the VIRUSBreakend table.
      """
      row_fields = mutation_info[constants.BODY]
      rows = []
      for row in row_fields:
          cells = [
              self._td(row[constants.GENUS]),
              self._td(row[constants.SPECIES]),
              self._td(row[constants.COVERAGE]),
              self._td(row[constants.LENGTH]),
              self._td(row[constants.MEANDEPTH]),
              self._td(row[constants.INTEGRATION])
          ]
          rows.append(self.table_row(cells))
      return rows

