"""Simple Djerba plugin for demonstration and testing: Example 1"""

from djerba.plugins.base import plugin_base

class main(plugin_base):

    def extract(self, config_section):
        data = {
            'plugin_name': 'demo1 plugin',
            'priority': 100,
            'attributes': ['clinical'],
            'merge_inputs': {
                'gene_information': [
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
