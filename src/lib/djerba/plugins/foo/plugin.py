from djerba.plugins.base import plugin_base

class main(plugin_base):

    def extract(self, config_section):
        data = {
            'plugin_name': 'foo plugin',
            'definitions': {},
            'description': {
                'title': 'Example plugin "foo"',
                'body': 'Demonstration plugin, writes placeholder text'
            },
            'treatment_options': [],
            'gene_information': [],
            'results': {},
        }
        return data

    def render(self, data):
        super().render(data)  # validate against schema
        self.logger.info("Rendering foo not yet implemented!")
        return "<h3>TODO foo plugin output goes here</h3>"
