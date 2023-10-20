"""collection of functions for rendering Djerba content in Mako"""

import djerba.plugins.genomic_landscape.msi.constants as constants
import re
from markdown import markdown
from time import strftime
from string import Template
from djerba.util.image_to_base64 import converter

class _html_builder:

    def assemble_biomarker_plot(self,biomarker,plot):
        template='<img id="{0}" style="width: 100%; " src="{1}"'
        cell = template.format(biomarker,plot)
        return(cell)

    def biomarker_table_rows(self, genomic_biomarker_args, purity):
        row_fields = genomic_biomarker_args[constants.BODY]
        rows = []
        for row in row_fields:
            cells = [
                self._td(row[constants.ALT]),
                self._td(row[constants.METRIC_ALTERATION]),
                self._td(self.assemble_biomarker_plot(row[constants.ALT],row[constants.METRIC_PLOT]))
            ]
            if row[constants.ALT] == "MSI" and purity < 50:
                cells = [
                    self._td(row[constants.ALT]),
                    self._td("NA"),
                    self._td("Cancer cell content &#8804; 50 &#37;, below threshold to call MS score")
                ]
            rows.append(self.table_row(cells))
        return rows
