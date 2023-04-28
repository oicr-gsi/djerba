"""Simple Djerba plugin for demonstration and testing: Example 1"""

from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 100

    def configure(self, config):
        config_section = config['demo1']
        priority_keys = [
            core_constants.CONFIGURE_PRIORITY,
            core_constants.EXTRACT_PRIORITY,
            core_constants.RENDER_PRIORITY
        ]
        for key in priority_keys:
            if not key in config_section:
                config_section[key] = '100'
        config_section[core_constants.CLINICAL] = 'true'
        config_section[core_constants.SUPPLEMENTARY] = 'false'
        config['demo1'] = config_section
        return config

    def extract(self, config_section):
        data = {
            'plugin_name': 'demo1 plugin',
            'priorities': self._get_priorities(config_section),
            'attributes': self._get_attributes(config_section),
            'merge_inputs': {
                'gene_information_merger': [
                    {
                        "Gene": "KRAS",
                        "Gene_URL": "https://www.oncokb.org/gene/KRAS",
                        "Chromosome": "12p12.1",
                        "Summary": "KRAS, a GTPase which functions as an upstream regulator of the MAPK and PI3K pathways, is frequently mutated in various cancer types including pancreatic, colorectal and lung cancers."
                    },
                    {
                        "Gene": "PIK3CA",
                        "Gene_URL": "https://www.oncokb.org/gene/PIK3CA",
                        "Chromosome": "3q26.32",
                        "Summary": "PIK3CA, the catalytic subunit of PI3-kinase, is frequently mutated in a diverse range of cancers including breast, endometrial and cervical cancers."
                    }
                ]
            },
            'results': {},
        }
        question = 'What do you get if you multiply six by nine?'
        self.workspace.write_string('question.txt', question)
        return data

    def render(self, data):
        super().render(data)  # validate against schema
        return "<h3>TODO demo1 plugin output goes here</h3>"
