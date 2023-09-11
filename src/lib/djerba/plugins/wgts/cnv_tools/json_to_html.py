"""collection of functions for rendering Djerba content in Mako"""

import djerba.render.constants as constants
import re
from markdown import markdown
from time import strftime
from string import Template
from djerba.util.image_to_base64 import converter

class html_builder:

    TR_START = '<tr style="text-align:left;">'
    TR_END = '</tr>'

    def _href(self, url, text):
        return '<a href="{0}">{1}</a>'.format(url, text)

    def _td(self, content, italic=False, width=None):
        # make a <td> table entry with optional attributes
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

    def oncogenic_CNVs_header(self, mutation_info):
        names = [
            constants.GENE,
            constants.CHROMOSOME,
            constants.ALTERATION,
            constants.ONCOKB
        ]
        if mutation_info[constants.HAS_EXPRESSION_DATA]:
            names.insert(self.EXPR_COL_INDEX_CNV, self.EXPR_SHORT_NAME)
        return self.table_header(names)

    def oncogenic_CNVs_rows(self, mutation_info):
        row_fields = mutation_info[constants.BODY]
        rows = []
        for row in row_fields:
            cells = [
                self._td(self._href(row[constants.GENE_URL], row[constants.GENE]), italic=True),
                self._td(row[constants.CHROMOSOME]),
                self._td(self._href(row[constants.ALT_URL], row[constants.ALTERATION])),
                self._td_oncokb(row['OncoKB level']),
            ]
            if mutation_info[constants.HAS_EXPRESSION_DATA]:
                metric = self._expression_display(row[constants.EXPRESSION_METRIC])
                cells.insert(self.EXPR_COL_INDEX_CNV, self._td(metric))
            rows.append(self.table_row(cells))
        return rows

    def process_oncokb_colours(self,oncokb_level):
        template = '<div  class="circle oncokb-level{0}">{0}</div>'  
        split_oncokb = oncokb_level.split(" ",2)
        oncokb_circle = template.format(split_oncokb[1])
        return(oncokb_circle)
        
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

    def table_header(self, names):
        items = ['<thead style="background-color:white">', '<tr>']
        for name in names:
            items.extend(['<th style="text-align:left;">', name, '</th>'])
        items.extend(['</tr>', '</thead>'])
        return ''.join(items)

    def table_row(self, cells):
        items = [self.TR_START, ]
        items.extend(cells)
        items.append(self.TR_END)
        return ''.join(items)
