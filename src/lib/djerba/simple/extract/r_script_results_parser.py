"""Parse output from the CGI-Tools legacy R script singleSample.r"""

# output consists of a directory of (mostly) TSV files
# parse attributes for each gene and sample
# output JSON compatible with the Elba schema

import csv
import json
import os
import djerba.simple.constants as constants

class r_script_results_parser:

    # file names
    DATA_MUTEX_ONCOGENIC = 'data_mutations_extended_oncogenic.txt'
    DATA_MUTEX_ONCOGENIC_PARSED = 'data_mutations_extended_oncogenic_parsed.json'
    DATA_CNA = 'data_CNA_oncoKBgenes_nonDiploid_annotated.txt'
    DATA_CNA_PARSED = 'data_CNA_oncoKBgenes_nonDiploid_annotated_parsed.json'

    # 0-based indices for data_mutations_extended_oncogenic.txt
    HUGO_SYMBOL_MUTEX = 0
    #CHROMOSOME = 4
    VARIANT_CLASSIFICATION = 8
    HGVSP_SHORT = 36
    WHIZBAM = 155

    # 0-based indices for data_CNA_oncoKBgenes_nonDiploid_annotated.txt
    HUGO_SYMBOL_CNA = 2
    ALTERATION = 4

    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.genes = {} # results by gene name

    def run(self):
        self.write_data_cna()
        self.write_data_mutations_extended_oncogenic()

    def write_data_cna(self):
        in_path = os.path.join(self.input_dir, self.DATA_CNA)
        parsed = []
        with open(in_path) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    first = False
                    continue # skip the header
                parsed.append(
                    {
                        constants.GENE: row[self.HUGO_SYMBOL_CNA],
                        constants.COPY_STATE: row[self.ALTERATION]
                    }
                )
        out_path = os.path.join(self.output_dir, self.DATA_CNA_PARSED)
        with open(out_path, 'w') as out_file:
            print(json.dumps(parsed, sort_keys=True, indent=4), file=out_file)

    def write_data_mutations_extended_oncogenic(self):
        in_path = os.path.join(self.input_dir, self.DATA_MUTEX_ONCOGENIC)
        parsed = []
        with open(in_path) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    first = False
                    continue # skip the header
                parsed.append(
                    {
                        constants.GENE: row[self.HUGO_SYMBOL_MUTEX],
                        constants.PROTEIN_CHANGE: row[self.HGVSP_SHORT],
                        constants.VARIANT_CLASSIFICATION: row[self.VARIANT_CLASSIFICATION],
                        constants.WHIZBAM_URL: row[self.WHIZBAM]
                    }
                )
        out_path = os.path.join(self.output_dir, self.DATA_MUTEX_ONCOGENIC_PARSED)
        with open(out_path, 'w') as out_file:
            print(json.dumps(parsed, sort_keys=True, indent=4), file=out_file)

