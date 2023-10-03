"""collection of functions for rendering Djerba TAR plugin content in Mako"""

import re
from markdown import markdown
from time import strftime
from string import Template
import djerba.plugins.tar.swgs.constants as swgs_constants
import djerba.plugins.tar.snv_indel.snv_indel_tools.constants as snv_constants

class html_builder():

  TR_START = '<tr style="text-align:left;">'
  TR_END = '</tr>'

    # ----------------------- Functions shared by more than one plugin ---------------------------
    
  def section_cells_begin(self, section_title, main_or_supp):
    # begin a cell structure with title in left-hand cell, body in right-hand cell
    permitted = ['main', 'supp']
    if main_or_supp not in permitted:
        msg = "Section type argument '{0}' not in {1}".format(main_or_supp, permitted)
        self.logger.error(msg)
        raise RuntimeError(msg)
    template = '<hr class="big-white-line" ><div class="twocell{0}"><div class="oneoftwocell{0}">{1}</div><div class="twooftwocell{0}" ><hr class="big-line" >'
    cell = template.format(main_or_supp,section_title)
    return cell

  def section_cells_end(self):
    # closes <div class="twocell... and <div class="twooftwocell...
    return "</div></div>\n"
    
  def _td(self, content, italic=False, width=None):
    """
    Makes a <td> table entry with optional attributes.
    Taken from the original json_to_html.py from the non-plugin Djerba.
    """
    attrs = []
    if italic:
        attrs.append('style="font-style: italic;"')
    if width:
        attrs.append('width="{0}%"'.format(width))
    if len(attrs) > 0:
        td = '<td {0}>{1}</td>'.format(' '.join(attrs), content)
    else:
        td = '<td>{0}</td>'.format(content)
    return td

  def _td_oncokb(self, level):
    # make a table cell with an OncoKB level symbol
    # permitted levels must have a format defined in style.css
    onc = 'Oncogenic'
    l_onc = 'Likely Oncogenic'
    p_onc = 'Predicted Oncogenic'
    level = re.sub('Level ', '', level) # strip off 'Level ' prefix, if any
    permitted_levels = ['1', '2', '3A', '3B', '4', 'R1', 'R2', onc, l_onc, p_onc]
    if not level in permitted_levels:
        msg = "Input '{0}' is not a permitted OncoKB level".format(level)
        raise RuntimeError(msg)
    if level in [onc, l_onc, p_onc]:
        shape = 'square'
    else:
        shape = 'circle'
    if level == onc:
        level = 'N1'
    elif level == l_onc:
        level = 'N2'
    elif level == p_onc:
        level = 'N3'
    div = '<div class="{0} oncokb-level{1}">{2}</div>'.format(shape, level, level)
    return self._td(div)

  def table_header(self, names):
    """
    Makes a table header (I think).
    Taken from the original json_to_html.py from the non-plugin Djerba
    """
    items = ['<thead style="background-color:white">', '<tr>']
    for name in names:
        items.extend(['<th style="text-align:left;">', name, '</th>'])
    items.extend(['</tr>', '</thead>'])
    return ''.join(items)

  def table_row(self, cells):
    """
    Makes a table row (I think).
    Taken from the original json_to_html.py from the non-plugin Djerba
    """
    items = [self.TR_START, ]
    items.extend(cells)
    items.append(self.TR_END)
    return ''.join(items)

  def _href(self, url, text):
    return '<a href="{0}">{1}</a>'.format(url, text)

  def k_comma_format(self,value):
    value_formatted = f'{value:,}'
    return(value_formatted)


  # ----------------------- sWGS-specific functions  ---------------------------
  
  def oncogenic_CNVs_header(self, mutation_info):
    names = [
        swgs_constants.GENE,
        swgs_constants.CHROMOSOME,
        swgs_constants.ALTERATION,
        swgs_constants.ONCOKB
    ]
    return self.table_header(names)

  def oncogenic_CNVs_rows(self, mutation_info):
    row_fields = mutation_info[swgs_constants.BODY]
    rows = []
    for row in row_fields:
        cells = [
            self._td(self._href(row[swgs_constants.GENE_URL], row[swgs_constants.GENE]), italic=True),
            self._td(row[swgs_constants.CHROMOSOME]),
            self._td(row[swgs_constants.ALTERATION]),
            self._td_oncokb(row[swgs_constants.ONCOKB]),
        ]
        rows.append(self.table_row(cells))
    return rows
  
  # ----------------------- snv_indel-specific functions  ---------------------------
  
  def oncogenic_small_mutations_and_indels_header(self, mutation_info, assay):
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
    return self.table_header(names)


  def oncogenic_small_mutations_and_indels_rows(self, mutation_info, assay):
    row_fields = mutation_info[snv_constants.BODY]
    rows = []
    for row in row_fields:
        depth = "{0}/{1}".format(row[snv_constants.TUMOUR_ALT_COUNT], row[snv_constants.TUMOUR_DEPTH])
        cells = [
            self._td(self._href(row[snv_constants.GENE_URL], row[snv_constants.GENE]), italic=True),
            self._td(row[snv_constants.CHROMOSOME]),
            self._td(self._href(row[snv_constants.PROTEIN_URL], row[snv_constants.PROTEIN])),
            self._td(row[snv_constants.MUTATION_TYPE]),
            self._td(row[snv_constants.VAF_PERCENT]),
            self._td(depth)
        ]
        if mutation_info[snv_constants.PASS_TAR_PURITY]:
            cells.append(self._td(row[snv_constants.COPY_STATE]))
        cells.append(self._td_oncokb(row[snv_constants.ONCOKB]))
        rows.append(self.table_row(cells))
    return rows

