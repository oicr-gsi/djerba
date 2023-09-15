"""Factory class to generate HTML structures"""

# adapted from json_to_html.py in djerba/v0.4.x

import re

class html_builder:

    TR_START = '<tr style="text-align:left;">'
    TR_END = '</tr>'

    @staticmethod
    def build_gene_url(gene):
        return 'https://www.oncokb.org/gene/'+gene

    @staticmethod
    def href(url, text):
        return '<a href="{0}">{1}</a>'.format(url, text)

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

