"""Djerba plugin for pwgs reporting"""
import os

from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup

class main(plugin_base):

    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        data = {
            'plugin_name': 'pwgs.analysis',
            'clinical': True,
            'failed': False,
            'merge_inputs': {
                'definitions': {},
                'description': {},
                'treatment_options': [],
                'gene_information': []
            },
            'results': {
                'outcome': config_section['outcome'],
                'significance_text': config_section['significance_text'],
                'TF': config_section['TF'],
                'sites_checked': config_section['sites_checked'],
                'reads_checked': config_section['reads_checked'],
                'sites_detected': config_section['sites_detected'],
                'reads_detected': config_section['reads_detected'],
                'p-value': config_section['p-value'],
                'hbc_n': config_section['hbc_n']
            }
        }
        return data

    def render(self, data):
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'html'
        ))
        report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
        mako_template = report_lookup.get_template(self.RESEARCH_TEMPLATE_NAME)
        try:
            html = mako_template.render(data)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            raise
        return html    
