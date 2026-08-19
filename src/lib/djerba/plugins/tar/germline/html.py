"""
HTML table construction for the TAR germline plugin.
"""

import djerba.plugins.tar.germline.constants as gc
from djerba.util.html import html_builder as hb


class germline_table_builder:

    NA_DISPLAY = 'VUS'

    @classmethod
    def _oncokb_cell(klass, level):
        if level in ('Unknown', 'NA', '', None):
            return hb.td(klass.NA_DISPLAY)
        return hb.td_oncokb(level)

    @classmethod
    def germline_header(klass):
        names = [
            gc.GENE,
            'Chr.',
            gc.PROTEIN,
            gc.MUTATION_TYPE,
            gc.VAF_NOPERCENT,
            gc.DEPTH,
            gc.CLIN_SIG_DISPLAY_KEY,
            gc.ONCOKB,
        ]
        return hb.thead(names)

    @classmethod
    def germline_rows(klass, row_fields):
        rows = []
        for row in row_fields:
            depth = "{0}/{1}".format(
                row[gc.TUMOUR_ALT_COUNT], row[gc.TUMOUR_DEPTH])
            cells = [
                hb.td(hb.href(row[gc.GENE_URL], row[gc.GENE]), italic=True),
                hb.td(row[gc.CHROMOSOME]),
                hb.td(hb.href(row[gc.PROTEIN_URL], row[gc.PROTEIN])),
                hb.td(row[gc.MUTATION_TYPE]),
                hb.td(row[gc.VAF_PERCENT]),
                hb.td(depth),
                hb.td(row[gc.CLIN_SIG_DISPLAY_KEY]),
                klass._oncokb_cell(row[gc.ONCOKB]),
            ]
            rows.append(hb.table_row(cells))
        return rows
