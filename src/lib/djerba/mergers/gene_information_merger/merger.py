"""Djerba merger for gene information"""

import re
import djerba.core.constants as core_constants
from djerba.mergers.base import merger_base
from djerba.util.render_mako import mako_renderer


class main(merger_base):

    GENE = 'Gene'
    GENE_URL = 'Gene_URL'
    SUMMARY = 'Summary'

    PRIORITY = 500
    MAKO_TEMPLATE_NAME = 'gene_information_template.html'
    SORT_KEY = GENE_URL

    def configure(self, config):
        config = self.apply_defaults(config)
        return config

    def table_header(self):
        names = [
            self.GENE,
            self.SUMMARY
        ]
        return self.thead(names)

    def table_rows(self, row_fields):
        rows = []
        for row in row_fields:
            # italicize the gene name where it appears in the summary
            # name must be:
            # - preceded by a space or start-of-string
            # - followed by a space or listed punctuation
            summary = re.sub('(^| ){0}[,.;: ]'.format(row[self.GENE]),
                             lambda m: '<i>{0}</i>'.format(m[0]),
                             row[self.SUMMARY])
            cells = [
                self.td(
                    self.href(row[self.GENE_URL], row[self.GENE]), italic=True
                ),
                self.td(summary)
            ]
            rows.append(self.tr(cells))
        return rows

    def render(self, inputs):
        self.validate_inputs(inputs)
        data = self.merge_and_sort(inputs, self.SORT_KEY)
        mako_input = {
            'rows': self.table_rows(data)
        }
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, mako_input)

    def specify_params(self):
        self.logger.debug("Specifying params for gene_information_merger")
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical,supplementary')
        self.set_priority_defaults(self.PRIORITY)
