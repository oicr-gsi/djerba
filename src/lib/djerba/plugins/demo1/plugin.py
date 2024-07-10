"""Simple Djerba plugin for demonstration and testing: Example 1"""

import logging
from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 200
    PLUGIN_VERSION = '1.0.0'

    # __init__ is inherited from the parent class

    def configure(self, config):
        config = self.apply_defaults(config)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        attributes = wrapper.get_my_attributes()
        self.check_attributes_known(attributes)
        my_integer = wrapper.get_my_int('integer')
        data = {
            'plugin_name': self.identifier+' plugin',
            'version': self.PLUGIN_VERSION,
            'priorities': wrapper.get_my_priorities(),
            'attributes': attributes,
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
            'results': {
                'integer': my_integer
            },
        }
        self.workspace.write_string('integer.txt', str(my_integer))
        return data

    def render(self, data):
        super().render(data)  # validate against schema
        number = data['results']['integer']
        output = [
            "<h1>Demonstration: Part 1</h1>",
            "<h2>Integer input: {0}</h2>".format(number),
            "<hr/>"
        ]
        return "\n".join(output)

    def specify_params(self):
        self.logger.debug("Specifying params for plugin demo1")
        self.add_ini_required('integer')
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)
