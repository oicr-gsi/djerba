"""Search for Djerba inputs"""

# proof-of-concept -- find a MAF file from provenance

# TODO:
# - find MAF file
# - (optionally) link file
# - add file to INI (or other config) for preprocessor
# - preprocess file to extract MAF metrics
# - supply metrics (eg. as JSON) to final output


import subprocess
import tempfile
import pandas as pd

class searcher:

    TMP_PROVENANCE_FILENAME = 'provenance_subset.tsv'
    
    def __init__(self, provenance_path, project, donor):
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_simple_')
        self.tmp_provenance_path = os.path.join(self.tmp.name, self.TMP_PROVENANCE_FILENAME)
        # could do this in Python, but UNIX utilities are faster
        cmd = [
            'zcat', provenance_path,
            '|',
            'awk', '-F "\t"',  
            '-v', 'p='+project, 'd='+donor,
            '($2 == p) && ($8 == d) && ($23 != "Illumina_MiSeq")',
            '>', self.tmp_provenance_path
        ]
        subprocess.run(cmd)
        self.df = None
        # TODO use pandas to read the provenance subset into a dataframe
        # methods can then scan provenance for desired data

    def _parse_path(self, analysis_unit, workflow, suffix, exclude=None):
        # get the desired path from the provenance dataframe
        # exclude is a list of [column, pattern] pairs; reject if a match is found
        # suffix = suffix of file path
        # note that columns are zero-indexed in pandas
        # if multiple results, sort and return one?
        # useful 1-indexed provenance columns:
        # 31 = workflow
        # 38 = tumor_only
        # 13,18,38,47 = analysis_unit
        pass

    def cleanup(self):
        self.tmp.cleanup()

    def parse_maf_path(self, analysis_unit):
        return self._parse_path(analysis_unit, 'variantEffectPredictor', '.maf.gz', [[37, 'tumor_only']])
