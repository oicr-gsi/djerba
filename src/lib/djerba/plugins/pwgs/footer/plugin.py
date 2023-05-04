"""Djerba plugin for pwgs footer"""
import os
import csv

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
import djerba.plugins.pwgs.analysis.plugin as analysis
import djerba.plugins.pwgs.sample.plugin as sample
from djerba.core.workspace import workspace

class main(plugin_base):

    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        data = {
            'plugin_name': 'pwgs.footer',
            'clinical': True,
            'failed': False,
            'merge_inputs': {
                'gene_information': []
            },
            'results': {
                'author': config_section['author']
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
        mako_template = report_lookup.get_template(constants.FOOTER_TEMPLATE_NAME)
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            raise
        return html    
    
