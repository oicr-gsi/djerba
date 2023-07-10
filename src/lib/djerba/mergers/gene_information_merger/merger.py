"""Djerba merger for gene information"""

import logging
import os
import re
import djerba.core.constants as core_constants
import djerba.render.constants as constants # TODO how do we handle constants in plugins?
from djerba.mergers.base import merger_base

class main(merger_base):

    PRIORITY = 300
    SCHEMA_FILENAME = 'gene_information_schema.json'
    SORT_KEY = 'Gene_URL'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def configure(self, config):
        config = self.apply_defaults(config)
        return config

    def table_header(self):
        names = [
            constants.GENE,
            constants.SUMMARY
        ]
        return self.thead(names)

    def table_rows(self, row_fields):
        rows = []
        for row in row_fields:
            # italicize the gene name where it appears in the summary
            # name must be:
            # - preceded by a space or start-of-string
            # - followed by a space or listed punctuation
            summary = re.sub('(^| ){0}[,.;: ]'.format(row[constants.GENE]),
                             lambda m: '<i>{0}</i>'.format(m[0]),
                             row[constants.SUMMARY])
            cells = [
                self.td(
                    self.href(row[constants.GENE_URL], row[constants.GENE]), italic=True
                ),
                self.td(summary)
            ]
            rows.append(self.tr(cells))
        return rows

    def render(self, inputs):
        self.validate_inputs(inputs)
        data = self.merge_and_sort(inputs, self.SORT_KEY)
        # TODO use CSS/Mako for appropriate template style
        html = [self.TABLE_START, self.table_header()]
        html.extend(self.table_rows(data))
        html.append(self.TABLE_END)
        return "\n".join(html)

    def specify_params(self):
        self.logger.debug("Specifying params for gene_information_merger")
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical,supplementary')
        self.set_priority_defaults(self.PRIORITY)
