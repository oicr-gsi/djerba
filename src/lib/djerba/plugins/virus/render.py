
import re
from markdown import markdown
from djerba.util.html import html_builder as hb

class html_builder:

  GENUS = 'Genus'
  SPECIES = 'Species'
  COVERAGE = 'Coverage'
  LENGTH = 'Length'
  MEANDEPTH = 'Mean depth'
  INTEGRATION = 'Integration'
  BODY = 'Body' 

  def virusbreakend_header(self):
    """
    Creates the header for the VIRUSBreakend table.
    """
    names = [
        self.GENUS,
        self.SPECIES,
        self.COVERAGE,
        self.LENGTH,
        self.MEANDEPTH,
        self.INTEGRATION
    ]
    return hb.thead(names)

  def virusbreakend_rows(self, mutation_info):
    """
    Creates the rows for the VIRUSBreakend table.
    """
    row_fields = mutation_info[self.BODY]
    rows = []
    for row in row_fields:
        cells = [
            hb.td(row[self.GENUS]),
            hb.td(row[self.SPECIES]),
            hb.td(row[self.COVERAGE]),
            hb.td(row[self.LENGTH]),
            hb.td(row[self.MEANDEPTH]),
            hb.td(row[self.INTEGRATION])
        ]
        rows.append(hb.table_row(cells))
    return rows
