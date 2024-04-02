
import re
from markdown import markdown
from djerba.util.html import html_builder as hb

class html_builder:

  # Header constants
  #SPECIES = 'Species'
  ASSIGNED = 'Assigned Name'
  NAME = 'Common Name'
  COVERAGE = 'Coverage'
  LENGTH = 'Viral Contig Length'
  INTEGRATION = 'Integration Breakpoints'

  # Extract constants
  #_SPECIES = 'name_species'
  _ASSIGNED = 'name_assigned'
  _NAME = 'common_name'
  _COVERAGE = 'coverage'
  _LENGTH = 'endpos'
  _INTEGRATION = 'integrations'
  _BODY = 'Body'

  def virusbreakend_header(self):
    """
    Creates the header for the VIRUSBreakend table.
    """
    names = [
        #self.SPECIES,
        self.ASSIGNED,
        self.NAME,
        self.LENGTH,
        self.COVERAGE,
        self.INTEGRATION,
    ]
    return hb.thead(names)

  def virusbreakend_rows(self, mutation_info):
    """
    Creates the rows for the VIRUSBreakend table.
    """
    row_fields = mutation_info[self._BODY]
    rows = []
    for row in row_fields:
        cells = [
            #hb.td(row[self._SPECIES]),
            hb.td(row[self._ASSIGNED]),
            hb.td(row[self._NAME]),
            hb.td(row[self._LENGTH]),
            hb.td(row[self._COVERAGE]),
            hb.td(row[self._INTEGRATION]),
        ]
        rows.append(hb.table_row(cells))
    return rows
