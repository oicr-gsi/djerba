"""Factory class to generate HTML structures"""

# adapted from json_to_html.py in djerba/v0.4.x

import re
from string import Template
from markdown import markdown

class html_builder:

    TABLE_START = '<table border=1>'
    TABLE_END = '</table>'
    TR_START = '<tr style="text-align:left;">'
    TR_END = '</tr>'

    @staticmethod
    def build_alteration_url(gene, alteration, cancer_code):
        base = 'https://www.oncokb.org/gene'
        return '/'.join([base, gene, alteration, cancer_code])

    @staticmethod
    def build_fusion_url(genes, oncotree_code):
        url = 'https://www.oncokb.org/gene/{0}/Fusion/{1}'.format(
            '-'.join(genes),
            oncotree_code
        )
        return url
    
    @staticmethod
    def build_onefusion_url(gene, oncotree_code):
        url = 'https://www.oncokb.org/gene/{0}/Fusion/{1}'.format(
            gene,
            oncotree_code
        )
        return url

    @staticmethod
    def build_gene_url(gene):
        return 'https://www.oncokb.org/gene/'+gene

    @staticmethod
    def expression_display(expr):
        if expr==None:
            return 'NA'
        else:
            return display_bar_maker(0, 100).get_bar_element(round(expr*100))

    @staticmethod
    def href(url, text):
        return '<a href="{0}">{1}</a>'.format(url, text)

    @staticmethod
    def k_comma_format(value):
        value_formatted = f'{value:,}'
        return(value_formatted)

    @staticmethod
    def make_ordinal(n):
        '''
        Convert an integer into its ordinal representation::

            make_ordinal(0)   => '0th'
            make_ordinal(3)   => '3rd'
            make_ordinal(122) => '122nd'
            make_ordinal(213) => '213th'
        '''
        n = int(n)
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return str(n) + suffix

    @staticmethod
    def markdown_to_html(markdown_string):
        return markdown(markdown_string)
    
    @staticmethod
    def section_cells_begin(section_title, is_main, no_hr_after=False):
        # begin a cell structure with title in left-hand cell, body in right-hand cell
        template = '<hr class="big-white-line" ><div class="twocell{0}">'+\
                '<div class="oneoftwocell{0}"><h{1}>{2}</h{1}></div>'+\
                '<div class="twooftwocell{0}" >'
        if is_main:
            class_suffix = 'main'
            rank = '2'
        else:
            class_suffix = 'supp'
            rank = '3'
        if no_hr_after:
            pass
        else:
            template = template + '<hr class="big-line" >'
        cell_begin = template.format(class_suffix, rank, section_title)
        return cell_begin

    @staticmethod
    def section_cells_end():
        # closes <div class="twocell... and <div class="twooftwocell...
        return "</div></div>\n"
    
    @staticmethod
    def table_row(cells):
        items = [html_builder.TR_START, ]
        items.extend(cells)
        items.append(html_builder.TR_END)
        return ''.join(items)

    @staticmethod
    def td(content, italic=False):
        if italic:
            content = '<i>{0}</i>'.format(content)
        return '<td>{0}</td>'.format(content)

    @staticmethod
    def td_oncokb(level):
        # make a table cell with an OncoKB level symbol
        # permitted levels must have a format defined in style.css
        level = re.sub('Level ', '', level) # strip off 'Level ' prefix, if any
        permitted_levels = ['1', '2', '3A', '3B', '4', 'R1', 'R2', 'N1', 'N2', 'N3','P']
        if not level in permitted_levels:
            msg = "Input '{0}' is not a permitted OncoKB level".format(level)
            raise RuntimeError(msg)
        if level in ['N1', 'N2', 'N3','P']:
            shape = 'square'
        else:
            shape = 'circle'
        div = '<div class="{0} oncokb-level{1}">{2}</div>'.format(shape, level, level)
        return html_builder.td(div)

    @staticmethod
    def thead(names):
        items = ['<thead style="background-color:white">', '<tr>']
        for name in names:
            items.extend(['<th style="text-align:left;">', name, '</th>'])
        items.extend(['</tr>', '</thead>'])
        return ''.join(items)

    @staticmethod
    def tr(cells):
        items = ['<tr style="text-align:left;">', ]
        items.extend(cells)
        items.append('</tr>')
        return ''.join(items)

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
        # min_val and max_val define the range of permitted inputs (defaults to percentile)
        # blue_max and red_min are between 0 and 1
        # the permitted range is scaled to find locations of blue_max and red_min
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
