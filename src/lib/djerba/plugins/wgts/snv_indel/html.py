"""Methods to generate SNV/indel html"""

import djerba.core.constants as core_constants
import djerba.plugins.wgts.snv_indel.constants as sic
from djerba.util.html import html_builder as hb
from djerba.util.variant_sorter import variant_sorter as var_sort
from djerba.util.expression_reader import expression_reader as xr

class snv_indel_table_builder:

    INSERT_COL_INDEX = 6
    EXPR_COL_TITLE = 'Expr. (%)'
    LOH_COL_TITLE = 'LOH'

    @classmethod
    def make_header(klass, mutation_info):
        # output between 7 and 9 columns
        # insert copy state (if any), then expression (if any)
        names = [
            'Gene',
            'Chr.',
            'Protein',
            'Type',
	    'VAF',
	    'Depth',
	    'OncoKB'
        ]
        if mutation_info[sic.HAS_LOH_DATA]:
            names.insert(klass.INSERT_COL_INDEX, klass.LOH_COL_TITLE)
        if mutation_info[sic.HAS_EXPRESSION_DATA]:
            names.insert(klass.INSERT_COL_INDEX, klass.EXPR_COL_TITLE)
        return hb.thead(names)

    @classmethod
    def make_rows(klass, mutation_info):
        row_fields = mutation_info[var_sort.BODY]
        rows = []
        for row in row_fields:
            cells = [
                hb.td(hb.href(row[var_sort.GENE_URL], row[var_sort.GENE]), italic=True),
                hb.td(row[var_sort.CHROMOSOME]),
                hb.td(hb.href(row[sic.PROTEIN_URL], row[sic.PROTEIN])),
                hb.td(row[sic.TYPE]),
                hb.td(row[sic.VAF]),
                hb.td(row[sic.DEPTH]),
                hb.td_oncokb(row[var_sort.ONCOKB])
            ]
            if mutation_info[sic.HAS_LOH_DATA]:
                if "X" in row[var_sort.CHROMOSOME]:
                    metric_cell = hb.td("NA")
                    cells.insert(klass.INSERT_COL_INDEX, metric_cell)
                else:
                    metric_cell = hb.td(row[sic.LOH])
                    cells.insert(klass.INSERT_COL_INDEX, metric_cell)
            if mutation_info[sic.HAS_EXPRESSION_DATA]:
                metric = row[xr.EXPRESSION_PERCENTILE]
                metric_cell = hb.td(hb.expression_display(metric))
                cells.insert(klass.INSERT_COL_INDEX, metric_cell)
            rows.append(hb.tr(cells))
        return rows

