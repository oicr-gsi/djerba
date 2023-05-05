"""Simple Djerba plugin for demonstration and testing: Example 2"""

import logging
from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 200

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_ini_required('demo2_param')
        self.set_ini_default('question', 'question.txt')
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_priorities(self.DEFAULT_CONFIG_PRIORITY)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
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
                'answer': wrapper.get_my_string('demo2_param'),
                'question': self.workspace.read_string(
                    wrapper.get_my_string('question')
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
