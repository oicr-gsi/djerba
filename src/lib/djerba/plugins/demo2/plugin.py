"""Simple Djerba plugin for demonstration and testing: Example 2"""

from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants

class main(plugin_base):

    def configure(self, config_section):
        priority_keys = [
            core_constants.CONFIGURE_PRIORITY,
            core_constants.EXTRACT_PRIORITY,
            core_constants.RENDER_PRIORITY
        ]
        for key in priority_keys:
            if not key in config_section:
                config_section[key] = '200'
        config_section[core_constants.CLINICAL] = 'true'
        config_section[core_constants.SUPPLEMENTARY] = 'false'
        config_section['question'] = 'question.txt'
        return config_section

    def extract(self, config_section):
        data = {
            'plugin_name': 'demo2 plugin',
            'priorities': self._get_priorities(config_section),
            'attributes': self._get_attributes(config_section),
            'merge_inputs': {
                'gene_information_merger': [
                    {
                        "Gene": "PIK3CA",
                        "Gene_URL": "https://www.oncokb.org/gene/PIK3CA",
                        "Chromosome": "3q26.32",
                        "Summary": "PIK3CA, the catalytic subunit of PI3-kinase, is frequently mutated in a diverse range of cancers including breast, endometrial and cervical cancers."
                    },
                    {
                        "Gene": "PIK3CB",
                        "Gene_URL": "https://www.oncokb.org/gene/PIK3CB",
                        "Chromosome": "3q22.3",
                        "Summary": "PIK3CB, a catalytic subunit of PI3-kinase, is altered by amplification or mutation in various cancer types."
                    }
                ]
            },
            'results': {
                'answer': config_section['demo2_param'],
                'question': self.workspace.read_string(config_section['question'])
            }
        }
        return data

    def render(self, data):
        output = [
            "<h1>The Answer is: {0}</h1>".format(data['results']['answer']),
            "<h1>The Question is: {0}</h1>".format(data['results']['question'])
            ]
        return "\n".join(output)
