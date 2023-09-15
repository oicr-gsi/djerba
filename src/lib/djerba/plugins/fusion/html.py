"""Method to generate fusion table html"""

from djerba.plugins.fusion.plugin import main as plugin
from djerba.util.html import html_builder as hb

def make_row_html(row):
    if re.search('intragenic', row[plugin.FUSION]): # omit intragenic fusions
        return None
    else:
        cells = [
            hb.td(hb.href(row[plugin.GENE_URL], row[plugin.GENE]), italic=True),
            hb.td(row[plugin.CHROMOSOME]),
            hb.td(row[plugin.FUSION]),
            hb.td(row[plugin.FRAME]),
            hb.td(row[plugin.MUTATION_EFFECT]),
            hb.td_oncokb(row[plugin.ONCOKB])
        ]
        return hb.table_row(cells)
