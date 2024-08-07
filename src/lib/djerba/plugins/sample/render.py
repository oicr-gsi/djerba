"""collection of functions for rendering Djerba content in Mako"""

import djerba.plugins.sample.constants as constants
import re
from markdown import markdown
from string import Template
from djerba.util.image_to_base64 import converter

class sample_html_builder:

    def sample_information_and_quality_rows(self, sample_args):
        widths = [[30,5], [15,25]]
        key_groups = [
            [constants.ONCOTREE_CODE, constants.TUMOUR_SAMPLE_TYPE],
            [constants.CALLABILITY_PERCENT, constants.COVERAGE_MEAN],
            [constants.EST_CANCER_CELL_CONTENT, constants.EST_PLOIDY]
        ]
        return self.key_value_table_rows(sample_args, key_groups, widths)

    def key_value_table_rows(self, args, key_groups, widths):
        """Make a table to show key/value fields, with varying column widths"""
        flattened = [k for group in key_groups for k in group]
        values = {}
        for key in flattened:
            # strings such as "Unknown" are permissible for purity/ploidy/coverage/callability
            if key in [constants.EST_PLOIDY, constants.COVERAGE_MEAN, constants.CALLABILITY_PERCENT] \
                 and (isinstance(args[key], float) or isinstance(args[key], int)):
                value = "{:0.1f}".format(args[key])
            elif key == constants.EST_CANCER_CELL_CONTENT and (isinstance(args[key], float) or isinstance(args[key], int)):
                value = str(int(round(args[key], 0)))
            else:
                value = args.get(key)
            values[key] = value
        rows = []
        for key_group in key_groups:
            row_items = ['<tr>']
            total = len(key_group)
            for i in range(total):
                width = widths[i]
                key = key_group[i]
                value = values[key]
                template = '<td width="{0}%">{1}:</td><td width="{2}%" >{3}</td>'
                cell = template.format(width[0], key, width[1], value)
                row_items.append(cell)
            row_items.append('</tr>')
            rows.append("\n".join(row_items))
        return rows
