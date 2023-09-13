"""Factory class to generate HTML structures"""

# adapted from json_to_html.py in djerba/v0.4.x

import re

class html_builder:

    TABLE_START = '<table border=1>'
    TABLE_END = '</table>'

    @staticmethod
    def href(url, text):
        return '<a href="{0}">{1}</a>'.format(url, text)

    @staticmethod
    def make_ordinal(n):
        '''
        Convert an integer into its ordinal representation::

            make_ordinal(0)   => '0th'
            make_ordinal(3)   => '3rd'
            make_ordinal(122) => '122nd'
            make_ordinal(213) => '213th'
        '''
        try:
            n = int(n)
        except TypeError as err:
            msg = "Cannot convert ordinal input '{0}' to an integer".format(n)
            raise DjerbaHtmlError(msg) from err
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return str(n) + suffix

    
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

class DjerbaHtmlError(Exception):
    pass
