
import djerba.plugins.genomic_landscape.constants as constants
from djerba.util.html import html_builder as hb
from markdown import markdown
from string import Template

class html_builder:

    def assemble_biomarker_plot(self,biomarker,plot):
        template='<img id="{0}" style="width: 100%; " src="{1}"'
        cell = template.format(biomarker,plot)
        return(cell)

    def biomarker_table_rows(self, biomarkers, can_report_hrd, can_report_msi):
        rows = []
        for marker, info in biomarkers.items():
            if marker == "HRD" and not can_report_hrd:
                cells = [
                    hb.td(info[constants.ALT]),
                    hb.td("NA"),
                    hb.td("Cancer cell content below threshold to evaluate HRD; must be &#8805;50&#37; for FFPE samples, &#8805;30&#37; otherwise")
                ]
            elif marker == "MSI" and not can_report_msi:
                cells = [
                    hb.td(info[constants.ALT]),
                    hb.td("NA"),
                    hb.td("Cancer cell content below threshold to call MS score; must be &#8805;50&#37;")
                ]
            else:
                cells = [
                    hb.td(info[constants.ALT]),
                    hb.td(info[constants.METRIC_ALTERATION]),
                    hb.td(self.assemble_biomarker_plot(info[constants.ALT], info[constants.METRIC_PLOT]))
                ]
            rows.append(hb.table_row(cells))
        return rows

