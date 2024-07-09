"""Simple Djerba plugin for demonstration and testing: Example 2"""

import logging
from time import strftime
from djerba.plugins.base import plugin_base
import djerba.core.constants as core_constants

class main(plugin_base):

    PRIORITY = 300
    PLUGIN_VERSION = '1.0.0'

    # __init__ inherited from parent class

    def configure(self, config):
        config = self.apply_defaults(config)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        contents = self.workspace.read_string(wrapper.get_my_string('integer_file'))
        integer_1 = int(contents.strip())
        integer_2 = wrapper.get_my_int('integer_2')
        integer_sum = integer_1 + integer_2
        integer_diff = integer_1 - integer_2
        data = {
            'plugin_name': self.identifier+' plugin',
            'version': self.PLUGIN_VERSION,
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
                'integer_1': integer_1,
                'integer_2': integer_2,
                'sum': integer_sum,
                'diff': integer_diff,
                'date': strftime('%Y-%m-%d'),
                'author': wrapper.get_core_string('author')
            }
        }
        return data

    def render(self, data):
        super().render(data)  # validate against schema
        integer_1 = data['results']['integer_1']
        integer_2 = data['results']['integer_2']
        integer_sum = data['results']['sum']
        integer_diff = data['results']['diff']
        credit = "Demonstration run by {0} on {1}".format(
            data['results']['author'],
            data['results']['date']
        )
        output = [
            "<h1>Demonstration: Part 2</h1>",
            "<h2>SECOND INTEGER INPUT: {0}</h2>".format(integer_2),
            "<h2>{0}+{1}={2}</h2>".format(integer_1, integer_2, integer_sum),
            "<h2>{0}-{1}={2}</h2>".format(integer_1, integer_2, integer_diff),
            "<hr/><h3>{0}</h3>".format(credit),
            "<hr/>"
        ]
        return "\n".join(output)

    def specify_params(self):
        self.logger.debug("Specifying params for plugin demo2")
        self.add_ini_required('integer_2')
        self.set_ini_default('integer_file', 'integer.txt')
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)
