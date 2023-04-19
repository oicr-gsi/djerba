"""Djerba plugin for pwgs sample reporting"""
import os
import csv
import logging
from decimal import Decimal

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.logger import logger

class main(plugin_base):

    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        self.logger.info("PWGS: No extracting necessary")       
        data = {
            'plugin_name': 'pwgs.sample',
            'clinical': True,
            'failed': False,
            'merge_inputs': {
                'gene_information': []
            },
            'results': {
                'median_insert_size': config_section[constants.INSERT_SIZE],
                'tumour_fraction': config_section[constants.TUMOUR_FRACTION_READS],
                'coverage': config_section[constants.COVERAGE],
                'primary_snv_count': config_section[constants.SNV_COUNT]
            }
        }
        return data

    def render(self, data):
        args = data
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'html'
        ))
        report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
        mako_template = report_lookup.get_template(constants.SAMPLE_TEMPLATE_NAME)
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            raise
        return html    