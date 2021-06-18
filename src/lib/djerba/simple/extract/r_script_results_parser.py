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
    
    # 0-based indices for data_mutations_extended_oncogenic.txt
    HUGO_SYMBOL = 0
    CHROMOSOME = 4
    WHIZBAM = 155
    
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.genes = {} # results by gene name

    def run(self):
        self.write_data_mutations_extended_oncogenic()

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
                gene = row[self.HUGO_SYMBOL]
                chromosome = row[self.CHROMOSOME]
                whizbam = row[self.WHIZBAM]
                parsed.append(
                    {
                        constants.GENE: gene,
                        constants.CHROMOSOME: chromosome,
                        constants.WHIZBAM_URL: whizbam
                    }
                )
        out_path = os.path.join(self.output_dir, self.DATA_MUTEX_ONCOGENIC_PARSED)
        with open(out_path, 'w') as out_file:
            print(json.dumps(parsed, sort_keys=True, indent=4), file=out_file)

