"""
Constants for the IMMAGINE table plugin.
"""

# Cytogenetic Alterations
MONOSOMY_13 = 'monosomy_chr_13'
MONOSOMY_14 = 'monosomy_chr_14'
MONOSOMY_17 = 'monosomy_chr_17'
DEL_1P = 'chr_1p_deletion'
DEL_17P = 'chr_17p_deletion'
AMP_1P = 'chr_1p_gain_or_amp'
HYPERDIPLOIDY = 'hyperdiploidy'
BI_DEL_1P32 = 'biallelic_deletion_1p32'
MONO_DEL_1P32 = 'monoallelic_deletion_1p32'
CYTOGEN_ALTS = 'cytogenetic_alterations'

# High risk
HIGH_RISK = "high_risk_myeloma"

# TP53 alteration
P53_ALT = "p53_SNV_or_CNV"

# Parameter names
DATA_MUTATIONS_FILE = 'mutations_file'
DATA_CNA_FILE = 'cna_file'
DATA_EXPRESSION_FILE = 'expression_file'

# File names
DATA_MUTATIONS_TXT = 'data_mutations_extended.txt'
DATA_CNA_TXT = 'purple.data_CNA.txt'
#DATA_CNA_TXT = 'data_CNA.txt'
DATA_EXPRESSION_TXT = 'data_expression_percentile_tcga.txt'

# List of PARPi genes


GENES = ["TP53", "MYC", "NRAS", "KRAS", "CDK2NC", "NFKB1", "NFKB2", "RB1", "BRAF", "CDK6", "ATM", "TNFRSF17", "CD38", "CRBN", "FCRH5", "FGFR3", "GPRC5D"] 

#PARPI_GENES = {'ABCB1': {"Copy Number": "Homozygous Deletion", "Expression Percentile": True},
#               'AKT1': {"Mutation Type": True, "Expression Percentile": True},
#               'ATM': {"Mutation Type": True, "Expression Percentile": True},
#               'ATR': {"Mutation Type": True, "Expression Percentile": True},
#               'BRCA1': {"Mutation Type": True, "Copy Number": "Homozygous Deletion", "Expression Percentile": True},
#               'BRCA2': {"Mutation Type": True, "Copy Number": "Homozygous Deletion", "Expression Percentile": True},
#               'CCNE1': {"Copy Number": "Gain"},
#               'CDC25A': {"Expression Percentile": True},
#               'CDC25C': {"Expression Percentile": True},
#               'CHEK1': {"Expression Percentile": True},
#               'CHEK2': {"Expression Percentile": True},
#               'KMT2C': {"Mutation Type": True},
#               'KMT2D': {"Mutation Type": True},
#               'PARG': {"Expression Percentile": True},
#               'PARP1': {"Mutation Type": True},
#               'PAXIP1': {"Copy Number": "Homozygous Deletion"},
#               'PIK3CA': {"Mutation Type": True, "Copy Number": "Gain"},
#               'SLFN11': {"Copy Number": "Homozygous Deletion"},
#               'MAPK1': {"Expression Percentile": True},
#               'MET': {"Copy Number": "Gain", "Expression Percentile": True},
#               'MTOR': {"Expression Percentile": True},
#               'VEGFA': {"Mutation Type": True, "Copy Number": "Gain"}}

# For extract
MUTATION_TYPE = 'Mutation Type'
MUTATION_ALT = 'Mutation Alteration'
MUTATION_FOUND = 'Mutation Found'
COPY_NUMBER = 'Copy Number'
EXPRESSION_PERCENTILE = 'Expression Percentile'
CHECKMARK = 'Matches Criteria'
