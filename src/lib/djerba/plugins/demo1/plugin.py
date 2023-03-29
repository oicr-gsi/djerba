"""Simple Djerba plugin for demonstration and testing: Example 1"""

from djerba.plugins.base import plugin_base

class main(plugin_base):

    def extract(self, config_section):
        data = {
            'plugin_name': 'demo1 plugin',
            'clinical': True,
            'failed': False,
            'merge_inputs': {
                'definitions': {},
                'description': {
                    'title': 'Example plugin "demo1"',
                    'body': 'Demonstration plugin, writes placeholder text'
                },
                'treatment_options': [],
                'gene_information': []
            },
            'results': {},
        }
        return data

    def render(self, data):
        super().render(data)  # validate against schema
        self.logger.info("Rendering demo1")
        return "<h3>TODO demo1 plugin output goes here</h3>"
