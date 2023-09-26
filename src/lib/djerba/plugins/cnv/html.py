"""Methods to generate CNV table html"""

import djerba.core.constants as core_constants
from djerba.plugins.cnv.plugin import main as plugin
from djerba.util.html import html_builder as hb

def make_table_header():  
    return hb.thead(['Gene', 'Chromosome', 'Expr. (%)', 'Alteration', 'OncoKB'])

def make_table_rows(body):
    table_rows = []
    for row in body:
        cells = [
            hb.td(hb.href(row[plugin.GENE_URL], row[plugin.GENE]), italic=True),
            hb.td(row[plugin.CHROMOSOME]),
            hb.td(hb.expression_display(row[plugin.EXPRESSION])),
            hb.td(row[plugin.ALTERATION]),
            hb.td_oncokb(row[core_constants.ONCOKB])
        ]
        table_rows.append(hb.table_row(cells))
    return table_rows
