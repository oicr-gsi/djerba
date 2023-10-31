"""Methods to generate SNV/indel html"""

import djerba.core.constants as core_constants
import djerba.plugins.wgts.snv_indel.constants as sic
from djerba.plugins.wgts.tools import wgts_tools
from djerba.util.html import html_builder as hb

EXPR_COL_INDEX_SMALL_MUT = 6
EXPR_SHORT_NAME = 'Expr. (%)'

def make_table_header(mutation_info):
    names = [
        'Gene',
        'Chr.',
        'Protein',
        'Type',
	'VAF',
	'Depth',
	'Copy State',
	'OncoKB'
    ]
    if mutation_info[sic.HAS_EXPRESSION_DATA]:
        names.insert(EXPR_COL_INDEX_SMALL_MUT, EXPR_SHORT_NAME)
    return hb.thead(names)

def make_table_rows(mutation_info):
    row_fields = mutation_info[wgts_tools.BODY]
    rows = []
    for row in row_fields:
        cells = [
            hb.td(hb.href(row[wgts_tools.GENE_URL], row[wgts_tools.GENE]), italic=True),
            hb.td(row[wgts_tools.CHROMOSOME]),
            hb.td(hb.href(row[sic.PROTEIN_URL], row[sic.PROTEIN])),
            hb.td(row[sic.TYPE]),
            hb.td(row[sic.VAF]),
            hb.td(row[sic.DEPTH]),
            hb.td(row[sic.COPY_STATE]),
            hb.td_oncokb(row[wgts_tools.ONCOKB])
        ]
        if mutation_info[sic.HAS_EXPRESSION_DATA]:
            metric = row[wgts_tools.EXPRESSION_PERCENTILE]
            metric_cell = hb.td(hb.expression_display(metric))
            cells.insert(EXPR_COL_INDEX_SMALL_MUT, metric_cell)
        rows.append(hb.tr(cells))
    return rows

