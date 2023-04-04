"""Factory class to generate HTML structures"""

# adapted from json_to_html.py in djerba/v0.4.x

import re

class html_builder:

    @staticmethod
    def href(self, url, text):
        return '<a href="{0}">{1}</a>'.format(url, text)
    
    @staticmethod
    def td(self, content):
        return '<td>{0}</td>'.format(content)

    @staticmethod
    def thead(self, names):
        items = ['<thead style="background-color:white">', '<tr>']
        for name in names:
            items.extend(['<th style="text-align:left;">', name, '</th>'])
        items.extend(['</tr>', '</thead>'])
        return ''.join(items)

    @staticmethod
    def tr(self, cells):
        items = ['<tr style="text-align:left;">', ]
        items.extend(cells)
        items.append('</tr>')
        return ''.join(items)
