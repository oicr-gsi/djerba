"""collection of functions for rendering Djerba TAR plugin content in Mako"""

import re
from markdown import markdown
from string import Template
from djerba.util.html import html_builder as hb
import djerba.plugins.tar.swgs.constants as swgs_constants
import djerba.plugins.tar.snv_indel.snv_indel_tools.constants as snv_constants

class html_builder():

  # ----------------------- sWGS-specific functions  ---------------------------
  
  def oncogenic_CNVs_header(self, mutation_info):
    names = [
        swgs_constants.GENE,
        swgs_constants.CHROMOSOME,
        swgs_constants.ALTERATION,
        swgs_constants.ONCOKB
    ]
    return hb.thead(names)

  def oncogenic_CNVs_rows(self, mutation_info):
    row_fields = mutation_info[swgs_constants.BODY]
    rows = []
    for row in row_fields:
        cells = [
            hb.td(hb.href(row[swgs_constants.GENE_URL], row[swgs_constants.GENE]), italic=True),
            hb.td(row[swgs_constants.CHROMOSOME]),
            hb.td(row[swgs_constants.ALTERATION]),
            hb.td_oncokb(row[swgs_constants.ONCOKB]),
        ]
        rows.append(hb.table_row(cells))
    return rows
  
  # ----------------------- snv_indel-specific functions  ---------------------------
  
  def oncogenic_small_mutations_and_indels_header(self, mutation_info):
    names = [
      snv_constants.GENE,
      'Chr.',
      snv_constants.PROTEIN,
      snv_constants.MUTATION_TYPE,
      snv_constants.VAF_NOPERCENT,
      snv_constants.DEPTH
    ]
    if mutation_info[snv_constants.PASS_TAR_PURITY]:
        names.append(snv_constants.COPY_STATE)
    names.append(snv_constants.ONCOKB)
    return hb.thead(names)


  def oncogenic_small_mutations_and_indels_rows(self, mutation_info):
    row_fields = mutation_info[snv_constants.BODY]
    rows = []
    for row in row_fields:
        depth = "{0}/{1}".format(row[snv_constants.TUMOUR_ALT_COUNT], row[snv_constants.TUMOUR_DEPTH])
        cells = [
            hb.td(hb.href(row[snv_constants.GENE_URL], row[snv_constants.GENE]), italic=True),
            hb.td(row[snv_constants.CHROMOSOME]),
            hb.td(hb.href(row[snv_constants.PROTEIN_URL], row[snv_constants.PROTEIN])),
            hb.td(row[snv_constants.MUTATION_TYPE]),
            hb.td(row[snv_constants.VAF_PERCENT]),
            hb.td(depth)
        ]
        if mutation_info[snv_constants.PASS_TAR_PURITY]:
            cells.append(hb.td(row[snv_constants.COPY_STATE]))
        cells.append(hb.td_oncokb(row[snv_constants.ONCOKB]))
        rows.append(hb.table_row(cells))
    return rows

