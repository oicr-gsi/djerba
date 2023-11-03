"""
Treatment options merger factory, to get correctly formatted JSON
"""

from djerba.mergers.factory import factory as factory_base
from djerba.mergers.treatment_options_merger.merger import main as merger
from djerba.util.html import html_builder


class factory(factory_base):

    def get_json(self, **kwargs):
        try:
            gene = kwargs['gene']
            result = {
                merger.TIER: kwargs['tier'],
                merger.ONCOKB_LEVEL: kwargs['level'],
                merger.TREATMENTS: kwargs['treatments'],
                merger.GENE: gene,
                merger.GENE_URL: html_builder.build_gene_url(gene),
                merger.ALTERATION: kwargs['alteration'],
                merger.ALTERATION_URL: kwargs['alteration_url']
            }
        except KeyError as err:
            msg = "Missing required argument for merger JSON? {0}".format(err)
            self.logger.error(msg)
            raise RuntimeError(msg) from err
        return result
