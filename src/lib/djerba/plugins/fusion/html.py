"""Method to generate fusion table html"""

import re
import djerba.core.constants as core_constants
from djerba.plugins.fusion.plugin import main as plugin
from djerba.util.html import html_builder as hb
from djerba.util.oncokb.tools import levels as oncokb_levels

def make_table_rows(rows):
    table_rows = []
    for row in rows:
        if re.search('intragenic', row[plugin.FUSION]): # omit intragenic fusions
            continue
        else:
            # fusion plugin records levels as numeric, not strings
            level = oncokb_levels.ALL_LEVELS[row.get(core_constants.ONCOKB)]
            cells = [
                hb.td(hb.href(row[plugin.GENE_URL], row[plugin.GENE]), italic=True),
                hb.td(row[plugin.CHROMOSOME]),
                hb.td(row[plugin.FUSION]),
                hb.td(row[plugin.FRAME]),
                hb.td(row[plugin.MUTATION_EFFECT]),
                hb.td_oncokb(level)
            ]
            table_rows.append(hb.table_row(cells))
    return table_rows
