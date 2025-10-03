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
            alteration = kwargs['alteration']
            
            # Check if the alteration is a fusion
            if alteration == "Fusion":
                gene_url = "NA" # We do not need gene_url for fusions
            else:
                gene_url = html_builder.build_gene_url(gene)

            result = {
                merger.TIER: kwargs['tier'],
                merger.ONCOKB_LEVEL: kwargs['level'],
                merger.TREATMENTS: kwargs['treatments'],
                merger.GENE: gene,
                merger.GENE_URL: gene_url,
                merger.ALTERATION: alteration,
                merger.ALTERATION_URL: kwargs['alteration_url']
            }
        except KeyError as err:
            msg = "Missing required argument for merger JSON? {0}".format(err)
            self.logger.error(msg)
            raise RuntimeError(msg) from err
        return result
