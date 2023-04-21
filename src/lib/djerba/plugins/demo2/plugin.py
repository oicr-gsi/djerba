"""Simple Djerba plugin for demonstration and testing: Example 2"""

from djerba.plugins.base import plugin_base

class main(plugin_base):

    def configure(self, config_section):
        config_section['demo2_param'] = '42'
        config_section['question'] = 'question.txt'
        return config_section

    def extract(self, config_section):
        data = {
            'plugin_name': 'demo2 plugin',
            'priority': 200,
            'attributes': ['clinical'],
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
