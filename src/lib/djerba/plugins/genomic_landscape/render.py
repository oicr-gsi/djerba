
import djerba.plugins.genomic_landscape.constants as constants
from djerba.util.html import html_builder as hb
from markdown import markdown
from string import Template

class html_builder:

    def assemble_biomarker_plot(self,biomarker,plot):
        template='<img id="{0}" style="width: 100%; " src="{1}"'
        cell = template.format(biomarker,plot)
        return(cell)

    def biomarker_table_rows(self, biomarkers, purity):
        rows = []
        for marker, info in biomarkers.items():
            cells = [
                hb.td(info[constants.ALT]),
                hb.td(info[constants.METRIC_ALTERATION]),
                hb.td(self.assemble_biomarker_plot(info[constants.ALT], info[constants.METRIC_PLOT]))
            ]
            if marker == "MSI" and purity < 50:
                cells = [
                    hb.td(info[constants.ALT]),
                    hb.td("NA"),
                    hb.td("Cancer cell content &#8804; 50 &#37;, below threshold to call MS score")
                ]
            rows.append(hb.table_row(cells))
        return rows

    def make_ordinal(self,n):
        '''
        Convert an integer into its ordinal representation::

            make_ordinal(0)   => '0th'
            make_ordinal(3)   => '3rd'
            make_ordinal(122) => '122nd'
            make_ordinal(213) => '213th'
        '''
        n = int(n)
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return str(n) + suffix
