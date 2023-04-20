"""Djerba plugin for SNVs/indels"""

import csv
import os
import re
import djerba.extract.oncokb.constants as oncokb
import djerba.render.constants as rc
import djerba.util.constants as dc
from djerba.util.html import html_builder as hb
from djerba.extract.report_to_json import clinical_report_json_composer
from djerba.plugins.base import plugin_base

class main(plugin_base, clinical_report_json_composer):

    def __init__(self, log_level, log_path):
        super().__init__(log_level, log_path)
        self.data_dir = os.path.join(os.environ['DJERBA_BASE_DIR'], dc.DATA_DIR_NAME)
        self.cytoband_path = os.path.join(self.data_dir, 'cytoBand.txt')
        self.cytoband_map = self.read_cytoband_map()
        self.oncokb_levels = [self.reformat_level_string(level) for level in oncokb.ORDERED_LEVELS]
        self.likely_oncogenic_sort_order = self.oncokb_sort_order(oncokb.LIKELY_ONCOGENIC)

    
    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        results = self.generate_results(config_section)
        data = {
            "clinical": True,
            "failed": False,
            "merge_inputs": {
                "gene_information": []
            },
            "plugin_name": "SNVs and in/dels",
            "results": results
        }
        return data

    def generate_results(self, config_section):
        # read in small mutations; output rows for oncogenic mutations
        self.logger.debug("Building data for small mutations and indels table")
        rows = []
        mutation_copy_states = self.read_mutation_copy_states(config_section['cna_simple'])
        mutation_LOH_states = self.read_mutation_LOH(config_section['cna_aratio'])
        with open(config_section['data_path']) as data_file:
            for input_row in csv.DictReader(data_file, delimiter="\t"):
                gene = input_row[self.HUGO_SYMBOL_TITLE_CASE]
                cytoband = self.get_cytoband(gene)
                protein = input_row[self.HGVSP_SHORT]
                if 'splice' in protein:
                    protein = 'p.? (' + input_row[self.HGVSC] + ')'  
                row = {
                    rc.GENE: gene,
                    rc.GENE_URL: self.build_gene_url(gene),
                    rc.CHROMOSOME: cytoband,
                    rc.PROTEIN: protein,
                    rc.PROTEIN_URL: self.build_alteration_url(
                        gene, protein, config_section['oncotree_uc']
                    ),
                    rc.MUTATION_TYPE: re.sub(
                        '_', ' ', input_row[self.VARIANT_CLASSIFICATION]
                    ),
                    rc.EXPRESSION_METRIC: None,
                    rc.VAF_PERCENT: int(round(float(input_row[self.TUMOUR_VAF]), 2)*100),
                    rc.TUMOUR_DEPTH: int(input_row[rc.TUMOUR_DEPTH]),
                    rc.TUMOUR_ALT_COUNT: int(input_row[rc.TUMOUR_ALT_COUNT]),
                    rc.COPY_STATE: mutation_copy_states.get(gene, self.UNKNOWN),
                    rc.LOH_STATE: mutation_LOH_states[gene],
                    rc.ONCOKB: self.parse_oncokb_level(input_row)
                }
                rows.append(row)
        self.logger.debug("Sorting and filtering small mutation and indel rows")
        rows = list(filter(self.oncokb_filter, self.sort_variant_rows(rows)))
        results = {
            rc.HAS_EXPRESSION_DATA: False,
            rc.CLINICALLY_RELEVANT_VARIANTS: len(rows),
            rc.TOTAL_VARIANTS: int(config_section['total_variants']),
            rc.BODY: rows
        }
        return results

    def read_mutation_copy_states(self, in_path):
        # overrides method from report_to_json
        # convert copy state to human readable string; return mapping of gene -> copy state
        copy_state_conversion = {
            0: "Neutral",
            1: "Gain",
            2: "Amplification",
            -1: "Shallow Deletion",
            -2: "Deep Deletion"
        }
        copy_states = {}
        with open(in_path) as in_file:
            first = True
            for row in csv.reader(in_file, delimiter="\t"):
                if first:
                    first = False
                else:
                    [gene, category] = [row[0], int(row[1])]
                    copy_states[gene] = copy_state_conversion.get(category, self.UNKNOWN)
        return copy_states

    def read_mutation_LOH(self, in_path):
        # overrides method from report_to_json
        # convert A-allele ratio to LOH; return mapping of gene -> LOH
        loh_states = {}
        with open(in_path) as in_file:
            first = True
            for row in csv.reader(in_file, delimiter="\t"):
                if first:
                    first = False
                else:
                    [gene, aratio] = [row[0], float(row[1])]
                    if(aratio == 0.0):
                        lohcall = "Yes"
                    else:
                        lohcall = "No"   
                    loh_states[gene] = (lohcall+' ('+str(round(aratio,1))+')')
        return loh_states
    
    def render(self, data):
        super().render(data)  # validate against schema
        output = ["<h3>SNV/indel output (work in progress)</h3>"]
        output.append(hb.TABLE_START)
        output.append(hb.thead(['Chromosome', 'Gene', 'Protein']))
        for variant in data['results']['Body']:
            row = [
                hb.td(variant['Chromosome']),
                hb.td(variant['Gene']),
                hb.td(variant['Protein'])
            ]
            output.append(hb.tr(row))
        output.append(hb.TABLE_END)
        return "\n".join(output)
    
