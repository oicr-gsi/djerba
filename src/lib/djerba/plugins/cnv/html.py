"""Methods to generate CNV table html"""

import djerba.core.constants as core_constants
import djerba.plugins.cnv.constants as cnv
from djerba.util.html import html_builder as hb

def make_table_header():  
    return hb.thead(['Gene', 'Chromosome', 'Expr. (%)', 'Alteration', 'OncoKB'])

def make_table_rows(body):
    table_rows = []
    for row in body:
        cells = [
            hb.td(hb.href(row[cnv.GENE_URL], row[cnv.GENE]), italic=True),
            hb.td(row[cnv.CHROMOSOME]),
            hb.td(hb.expression_display(row[cnv.EXPRESSION_PERCENTILE])),
            hb.td(row[cnv.ALTERATION]),
            hb.td_oncokb(row[core_constants.ONCOKB])
        ]
        table_rows.append(hb.table_row(cells))
    return table_rows
