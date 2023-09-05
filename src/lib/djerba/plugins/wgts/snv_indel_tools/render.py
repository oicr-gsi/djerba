"""
This script describes a list of functions to render the Copy Number Variation data from the json into HTML.
"""

# IMPORTS
import re
from markdown import markdown
from time import strftime
from string import Template
import djerba.plugins.wgts.snv_indel_tools.constants as constants

class html_builder:
  
  TR_START = '<tr style="text-align:left;">'
  TR_END = '</tr>'
  EXPR_COL_INDEX_SMALL_MUT = 6 # position of expression column (if any) in small mutations table
  EXPR_COL_INDEX_CNV = 2 # position of expression column (if any) in cnv table
  EXPR_SHORT_NAME = 'Expr. (%)'
    
  # ------------------- TABLE FORMAT FUNCTIONS -------------------
  
  def section_cells_begin(self, section_title, main_or_supp):
    """
    Describes how the section cells begin.
    Taken from the original json_to_html.py from the non-plugin Djerba.
    
    Begin a cell structure with title in left-hand cell, body in right-hand cell
    """
    permitted = ['main', 'supp']
    if main_or_supp not in permitted:
        msg = "Section type argument '{0}' not in {1}".format(main_or_supp, permitted)
        self.logger.error(msg)
        raise RuntimeError(msg)
    template = '<hr class="big-white-line" ><div class="twocell{0}"><div class="oneoftwocell{0}">{1}</div><div class="twooftwocell{0}" ><hr class="big-line" >'
    cell = template.format(main_or_supp,section_title)
    return cell
  
  def section_cells_end(self):
    """
    Describes how the section cells end.
    Taken from the original json_to_html.py from the non-plugin Djerba.
    
    Closes <div class="twocell... and <div class="twooftwocell...
    """
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
  # ----------------------- CNV FUNCTIONS ----------------------
      
  def oncogenic_small_mutations_and_indels_header(self, mutation_info):
    names = [
      constants.GENE,
      'Chr.',
      constants.PROTEIN,
      constants.MUTATION_TYPE,
      constants.VAF_NOPERCENT,
      constants.DEPTH,
      constants.COPY_STATE,
      constants.ONCOKB
    ]

    if mutation_info[constants.HAS_EXPRESSION_DATA]:
        names.insert(self.EXPR_COL_INDEX_SMALL_MUT, self.EXPR_SHORT_NAME)
    return self.table_header(names)


  def oncogenic_small_mutations_and_indels_rows(self, mutation_info):
    row_fields = mutation_info[constants.BODY]
    rows = []
    for row in row_fields:
        depth = "{0}/{1}".format(row[constants.TUMOUR_ALT_COUNT], row[constants.TUMOUR_DEPTH])
        cells = [
            self._td(self._href(row[constants.GENE_URL], row[constants.GENE]), italic=True),
            self._td(row[constants.CHROMOSOME]),
            self._td(self._href(row[constants.PROTEIN_URL], row[constants.PROTEIN])),
            self._td(row[constants.MUTATION_TYPE]),
            self._td(row[constants.VAF_PERCENT]),
            self._td(depth),
            self._td(row[constants.COPY_STATE]),
            self._td_oncokb(row['OncoKB level'])
        ]
        if mutation_info[constants.HAS_EXPRESSION_DATA]:
            metric = self._expression_display(row[constants.EXPRESSION_METRIC])
            cells.insert(self.EXPR_COL_INDEX_SMALL_MUT, self._td(metric))
        rows.append(self.table_row(cells))
    return rows




  # ------------------------------- EXPRESSION ----------------------------

  def _expression_display(self, expr):
    if expr==None:
        return 'NA'
    else:
        bar_maker = display_bar_maker(0,100)
        return bar_maker.get_bar_element(round(expr*100))

    # -------------------- for making bars ------------------

class display_bar_maker:

    """
    Make a SVG display with a coloured dot on a horizontal bar
    Intended to represent a quantity in a table cell
    """

    BAR_OFFSET = 4  # offset of bar from left-hand border
    BAR_LENGTH = 30 # length of display bar, in pixels

    TEMPLATE = '<svg width="67" height="12"><text x="39" y="11" text-anchor="start" '+\
                'font-size="12" fill=${text_colour}>${value}</text><g><line x1="${bar_start}" '+\
                'y1="8" x2="${bar_end}" y2="8" style="stroke: gray; '+\
                'stroke-width: 2px;"></line><circle cx="${pos}" cy="8" r="3" '+\
                'fill="${circle_colour}"></circle></g></svg>'

    COLOUR_LOW = 'blue'
    COLOUR_HIGH = 'red'

    def __init__(self, min_val, max_val, blue_max=0.2, red_min=0.8):
        self.min_val = min_val
        self.max_val = max_val
        self.x_range = float(max_val - min_val)
        if self.x_range <= 0:
            raise RuntimeError("Invalid range: min={0}, max={1}".format(min_val, max_val))
        self.blue_max = blue_max
        self.red_min = red_min

    def get_circle_colour(self, x):
        if x <= self.blue_max:
            return self.COLOUR_LOW
        elif x >= self.red_min:
            return self.COLOUR_HIGH
        else:
            return 'gray'

    def get_text_colour(self, x):
        if x <= self.blue_max:
            return self.COLOUR_LOW
        elif x >= self.red_min:
            return self.COLOUR_HIGH
        else:
            return 'black'

    def get_circle_position(self, x):
        return x*self.BAR_LENGTH + self.BAR_OFFSET

    def get_bar_element(self, x):
        x_raw = x
        x = x / self.x_range
        if x < 0 or x > 1:
            raise ValueError("Input {0} out of range ({1}, {2})".format(x, self.min_val, self.max_val))
        params = {
            'value': x_raw,
            'bar_start': self.BAR_OFFSET,
            'bar_end': self.BAR_LENGTH+self.BAR_OFFSET,
            'pos': self.get_circle_position(x),
            'circle_colour': self.get_circle_colour(x),
            'text_colour': self.get_text_colour(x)
        }
        return Template(self.TEMPLATE).substitute(params)
