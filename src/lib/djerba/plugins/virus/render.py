
import re
from markdown import markdown
from djerba.util.html import html_builder as hb

class html_builder:

  # Header constants
  #GENUS = 'Genus'
  SPECIES = 'Species'
  ASSIGNED = 'Assigned Name'
  COVERAGE = 'Coverage'
  LENGTH = 'Viral Contig Length'
  INTEGRATION = 'Number of Integration Breakpoints'
  DRIVER = 'Driver Virus'

  # Extract constants
  #_GENUS = 'name_genus'
  _SPECIES = 'name_species'
  _ASSIGNED = 'name_assigned'
  _COVERAGE = 'coverage'
  _LENGTH = 'endpos'
  _INTEGRATION = 'integrations'
  _DRIVER = 'driver'
  _BODY = 'Body'

  def virusbreakend_header(self):
    """
    Creates the header for the VIRUSBreakend table.
    """
    names = [
        #self.GENUS,
        self.SPECIES,
        self.ASSIGNED,
        self.LENGTH,
        self.COVERAGE,
        self.INTEGRATION,
        self.DRIVER
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
            #hb.td(row[self._GENUS]),
            hb.td(row[self._SPECIES]),
            hb.td(row[self._ASSIGNED]),
            hb.td(row[self._LENGTH]),
            hb.td(row[self._COVERAGE]),
            hb.td(row[self._INTEGRATION]),
            hb.td(row[self._DRIVER])
        ]
        rows.append(hb.table_row(cells))
    return rows
