"""Djerba plugin for pwgs reporting"""
import os

from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.pwgs.constants as constants

class main(plugin_base):
    TEMPLATE_NAME = 'analysis_template.html'

    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        data = {
            'plugin_name': 'pwgs.analysis',
            'clinical': True,
            'failed': False,
            'merge_inputs': {
                'gene_information': []
            },
            'results': {
                'outcome': bool(config_section['outcome']),
                'significance_text': config_section['significance_text'],
                'TF': float(config_section['TF']),
                'sites_checked': int(config_section['sites_checked']),
                'reads_checked': int(config_section['reads_checked']),
                'sites_detected': int(config_section['sites_detected']),
                'reads_detected': int(config_section['reads_detected']),
                'p-value': float(config_section['p-value']),
                'hbc_n': int(config_section['hbc_n'])
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
        mako_template = report_lookup.get_template(self.TEMPLATE_NAME)
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            raise
        return html    
