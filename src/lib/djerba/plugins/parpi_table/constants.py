"""
Constants for the PARPi table plugin.
"""

# Parameter names
DATA_MUTATIONS_FILE = 'mutations_file'
DATA_CNA_FILE = 'cna_file'
DATA_EXPRESSION_FILE = 'expression_file'

# File names
DATA_MUTATIONS_TXT = 'data_mutations_extended.txt'
DATA_CNA_TXT = 'data_CNA.txt'
DATA_EXPRESSION_TXT = 'data_expression_percentile_tcga.txt'

# List of PARPi genes
PARPI_GENES = ['BRCA1',
               'BRCA2',
               'MLL3',
               'MLL4',
               'PAXIP1',
               'SLFN11',
               'AKT1',
               'ATM',
               'ATR',
               'CDC25A',
               'CDC25C',
               'CHEK1',
               'CHEK2',
               'MAPK',
               'MET',
               'mTOR',
               'PARG',
               'PARP1',
               'PIK3CA',
               'VEGFA',
               'MRD1']

# For extract
MUTATION_TYPE = 'Mutation Type'
COPY_NUMBER = 'Copy Number'
EXPRESSION_PERCENTILE = 'Expression Percentile'
