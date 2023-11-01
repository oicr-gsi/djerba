"""
Gene information merger factory, to get correctly formatted JSON
"""

from djerba.mergers.factory import factory as factory_base
from djerba.mergers.gene_information_merger.merger import main as merger
from djerba.util.html import html_builder


class factory(factory_base):

    def get_json(self, **kwargs):
        try:
            gene = kwargs['gene']
            summary = kwargs['summary']
        except KeyError as err:
            msg = "Missing required argument for merger JSON? {0}".format(err)
            self.logger.error(msg)
            raise RuntimeError(msg) from err
        result = {
            merger.GENE: gene,
            merger.GENE_URL: html_builder.build_gene_url(gene),
            merger.SUMMARY: summary
        }
        return result
