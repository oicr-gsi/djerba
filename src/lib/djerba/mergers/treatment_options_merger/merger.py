"""
Djerba merger for treatment options

This merger will:
- Read input from plugins
- Categorize treatments by tier: "Approved" or "Investigational"
- For each tier, sort by OncoKB level and then by gene name
- Output HTML header text and tables for "Approved" and "Investigational"

Mockup of therapy row output dictionary:
{
    "Tier": "Approved",
    "OncoKB level": 1,
	"Treatments": 'foobarzanib',
	"Gene": 'gene 1'
	"Gene_URL": 'http://example.com/gene1',
	"Alteration": 'protein 1',
	"Alteration_URL": 'http://example.com/protein1',
}
"""

import logging
import os
import re
import djerba.core.constants as core_constants
import djerba.render.constants as constants
from djerba.mergers.base import merger_base, DjerbaMergerError
from djerba.util.oncokb.tools import levels as oncokb
from djerba.util.render_mako import mako_renderer

class main(merger_base):

    MAKO_TEMPLATE_NAME = 'treatment_options_template.html'
    PRIORITY = 300

    # dictionary keywords
    APPROVED = 'Approved'
    INVESTIG = 'Investigational'
    TIER = 'Tier'
    ONCOKB_LEVEL = "OncoKB level"
    TREATMENTS = "Treatments"
    GENE = "Gene"
    GENE_URL = "Gene_URL"
    ALTERATION = "Alteration"
    ALTERATION_URL = "Alteration_URL"

    def configure(self, config):
        config = self.apply_defaults(config)
        return config

    @staticmethod
    def get_link(url, text):
        return '<a href="{0}">{1}</a>'.format(url, text)

    def get_therapy_info(self, tier_input):
        # deduplicate by oncokb level and alteration name (both together are a unique ID)
        k1 = self.ONCOKB_LEVEL
        k2 = self.ALTERATION
        try:
            unique_items = list({(v[k1], v[k2]):v for v in tier_input}.values())
        except KeyError as err:
            msg = "Missing required key(s) from merger input: {0}".format(err)
            self.logger.error(msg)
            self.logger.debug("Merger inputs: {0}".format(inputs))
            raise DjerbaMergerError from err
        # sort by oncokb level, then alteration name
        return sorted(unique_items, key = lambda x: (oncokb.oncokb_order(x[k1]), x[k2]))

    def render(self, inputs):
        self.validate_inputs(inputs)
        # categorize inputs, sort, and find totals
        # input is a list of lists, flatten into a single list
        flattened = [x for sublist in inputs for x in sublist]
        approved = []
        investig = []
        for item in flattened:
            tier = item[self.TIER]
            if tier == self.APPROVED:
                approved.append(item)
            elif tier == self.INVESTIG:
                investig.append(item)
            else:
                msg = "Unknown actionability tier: '{0}'".format(tier)
                self.logger.error(msg)
                raise DjerbaMergerError(msg)
        approved_therapies = self.get_therapy_info(approved)
        investig_therapies = self.get_therapy_info(investig)
        data = {
            'approved_total': len(approved_therapies),
            'investig_total': len(investig_therapies),
            'approved_therapies': approved_therapies,
            'investig_therapies': investig_therapies
        }
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

    def specify_params(self):
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical,supplementary')
        self.set_priority_defaults(self.PRIORITY)
