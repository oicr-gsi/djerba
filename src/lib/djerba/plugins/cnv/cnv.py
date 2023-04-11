"""Simple Djerba plugin for demonstration and testing: Example 1"""

from djerba.plugins.base import plugin_base

class main(plugin_base):

    def extract(self, config_section):
        data = {
            'plugin_name': 'cnv',
            'clinical': True,
            'failed': False,
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
            'results': {
            "Body": [
                {
                    "Alteration": "Amplification",
                    "Chromosome": "19q12",
                    "Expression Percentile": 0.2268,
                    "Gene": "CCNE1",
                    "Gene_URL": "https://www.oncokb.org/gene/CCNE1",
                    "OncoKB": "Level 4"
                },
                {
                    "Alteration": "Amplification",
                    "Chromosome": "7q21.2",
                    "Expression Percentile": 1.0,
                    "Gene": "CDK6",
                    "Gene_URL": "https://www.oncokb.org/gene/CDK6",
                    "OncoKB": "Oncogenic"
                },
                {
                    "Alteration": "Amplification",
                    "Chromosome": "3q26.32",
                    "Expression Percentile": 0.9192,
                    "Gene": "PIK3CA",
                    "Gene_URL": "https://www.oncokb.org/gene/PIK3CA",
                    "OncoKB": "Likely Oncogenic"
                },
                {
                    "Alteration": "Amplification",
                    "Chromosome": "3q27.3",
                    "Expression Percentile": 0.8234,
                    "Gene": "BCL6",
                    "Gene_URL": "https://www.oncokb.org/gene/BCL6",
                    "OncoKB": "Likely Oncogenic"
                },
                {
                    "Alteration": "Amplification",
                    "Chromosome": "19q13.2",
                    "Expression Percentile": 1.0,
                    "Gene": "AKT2",
                    "Gene_URL": "https://www.oncokb.org/gene/AKT2",
                    "OncoKB": "Likely Oncogenic"
                },
                {
                    "Alteration": "Amplification",
                    "Chromosome": "19q13.2",
                    "Expression Percentile": 1.0,
                    "Gene": "AXL",
                    "Gene_URL": "https://www.oncokb.org/gene/AXL",
                    "OncoKB": "Likely Oncogenic"
                }
            ],
            "Clinically relevant variants": 6,
            "Has expression data": true,
            "Total variants": 48
        },
        }
        return data

    def render(self, data):
        super().render(data)  # validate against schema
        self.logger.info("Rendering CNV information")
        return "<h3>TODO demo1 plugin output goes here</h3>"
