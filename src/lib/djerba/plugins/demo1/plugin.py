"""Simple Djerba plugin for demonstration and testing: Example 1"""

import logging
from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 100

    def __init__(self, workspace, identifier, log_level=logging.INFO, log_path=None):
        super().__init__(workspace, identifier, log_level, log_path)
        self.add_ini_required('question')
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)
        self.set_ini_default('dummy_file', None)

    def configure(self, config):
        config = self.apply_defaults(config)
        config = self.set_all_priorities(config, self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': self.get_my_priorities(config),
            'attributes': self.get_my_attributes(config),
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
