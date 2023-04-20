"""Factory class to generate HTML structures"""

# adapted from json_to_html.py in djerba/v0.4.x

import re

class html_builder:

    TABLE_START = '<table border=1>'
    TABLE_END = '</table>'
    VARIANTS_TABLE_START = '<table class="variants" width="100%">'

    @staticmethod
    def href(url, text):
        return '<a href="{0}">{1}</a>'.format(url, text)

    @staticmethod
    def report_section_start(title):
        start = '<hr class="big-white-line" ><div class="twocellmain">'+\
            '<div class="oneoftwocellmain">'+\
            '<h2>{0}</h2></div>'.format(title)+\
            '<div class="twooftwocellmain" ><hr class="big-line" >'
        return start

    @staticmethod
    def report_section_end():
        return '</div></div>'

    @staticmethod
    def td(content, italic=False):
        if italic:
            content = '<i>{0}</i>'.format(content)
        return '<td>{0}</td>'.format(content)

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
