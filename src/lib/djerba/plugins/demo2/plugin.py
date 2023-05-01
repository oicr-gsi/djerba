"""Simple Djerba plugin for demonstration and testing: Example 2"""

from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 200

    def configure(self, config):
        priority_keys = [
            core_constants.CONFIGURE_PRIORITY,
            core_constants.EXTRACT_PRIORITY,
            core_constants.RENDER_PRIORITY
        ]
        for key in priority_keys:
            if not self.has_my_param(config, key):
                config = self.set_my_param(config, key, self.DEFAULT_CONFIG_PRIORITY)
        config = self.set_my_param(config, core_constants.CLINICAL, True)
        config = self.set_my_param(config, core_constants.SUPPLEMENTARY, False)
        return config

    def extract(self, config):
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': self.get_my_priorities(config),
            'attributes': self.get_my_attributes(config),
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
                'answer': self.get_my_param_string(config, 'demo2_param'),
                'question': self.workspace.read_string(
                    self.get_my_param_string(config, 'question')
                )
            }
        }
        return data

    def render(self, data):
        output = [
            "<h1>The Answer is: {0}</h1>".format(data['results']['answer']),
            "<h1>The Question is: {0}</h1>".format(data['results']['question'])
            ]
        return "\n".join(output)
