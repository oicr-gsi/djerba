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
PARPI_GENES = {'ABCB1': {"Copy Number": "Homozygous Deletion", "Expression Percentile": True},
               'AKT1': {"Mutation Type": True, "Expression Percentile": True},
               'ATM': {"Mutation Type": True, "Expression Percentile": True},
               'ATR': {"Mutation Type": True, "Expression Percentile": True},
               'BRCA1': {"Mutation Type": True, "Copy Number": "Homozygous Deletion", "Expression Percentile": True},
               'BRCA2': {"Mutation Type": True, "Copy Number": "Homozygous Deletion", "Expression Percentile": True},
               'CCNE1': {"Copy Number": "Gain"},
               'CDC25A': {"Expression Percentile": True},
               'CDC25C': {"Expression Percentile": True},
               'CHEK1': {"Expression Percentile": True},
               'CHEK2': {"Expression Percentile": True},
               'KMT2C': {"Mutation Type": True},
               'KMT2D': {"Mutation Type": True},
               'PARG': {"Expression Percentile": True},
               'PARP1': {"Mutation Type": True},
               'PAXIP1': {"Copy Number": "Homozygous Deletion"},
               'PIK3CA': {"Mutation Type": True, "Copy Number": "Gain"},
               'SLFN11': {"Copy Number": "Homozygous Deletion"},
               'MAPK1': {"Expression Percentile": True},
               'MET': {"Copy Number": "Gain", "Expression Percentile": True},
               'MTOR': {"Expression Percentile": True},
               'VEGFA': {"Mutation Type": True, "Copy Number": "Gain"}}

# For extract
MUTATION_TYPE = 'Mutation Type'
COPY_NUMBER = 'Copy Number'
EXPRESSION_PERCENTILE = 'Expression Percentile'
CHECKMARK = 'Matches Criteria'
