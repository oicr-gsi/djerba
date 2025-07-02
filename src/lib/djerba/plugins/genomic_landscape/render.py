
import djerba.plugins.genomic_landscape.constants as constants
from djerba.util.html import html_builder as hb
from markdown import markdown
from string import Template

class html_builder:

    def assemble_biomarker_plot(self,biomarker,plot):
        template='<img id="{0}" style="width: 100%; " src="{1}"'
        cell = template.format(biomarker,plot)
        return(cell)

    def biomarker_table_rows(self, biomarkers, can_report_hrd, cant_report_hrd_reason, can_report_msi):
        rows = []
        for marker, info in biomarkers.items():
            if marker == "HRD" and not can_report_hrd and cant_report_hrd_reason:
                if cant_report_hrd_reason == "purity":
                    cells = [
                        hb.td(info[constants.ALT]),
                        hb.td("NA"),
                        hb.td("Cancer cell content below threshold to evaluate HRD; must be &#8805;50&#37; for FFPE samples, &#8805;30&#37; otherwise")
                    ]
                elif cant_report_hrd_reason == "coverage":
                    cells = [
                        hb.td(info[constants.ALT]),
                        hb.td("NA"),
                        hb.td("Coverage above threshold to evaluate HRD; must be &#8804;115X")
                    ]
                else:
                    msg = "Cannot report HRD reason: {0}. The only valid reasons for HRD to not be reported are purity and coverage".format(cant_report_hrd_reason)
                    self.logger.error(msg)
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

