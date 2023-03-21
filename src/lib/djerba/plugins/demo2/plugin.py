"""Simple Djerba plugin for demonstration and testing: Example 2"""

from djerba.plugins.base import plugin_base

class main(plugin_base):

    def extract(self, config_section):
        data = {
            'plugin_name': 'demo2 plugin',
            'definitions': {},
            'description': {
                'title': 'Example plugin "demo2"',
                'body': 'Demonstration plugin to output a well-known constant'
            },
            'treatment_options': [],
            'gene_information': [],
            'results': {
                'answer': config_section['demo2_param']
            }
        }
        return data

    def render(self, data):
        return "<h1>The Answer is: {0}</h1>".format(data['results']['answer'])
