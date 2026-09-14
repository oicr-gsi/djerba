"""
Constants for the IMMAGINE table plugin.
"""

# For plugin
HAS_EXPRESSION_DATA = 'has_expression_data'

# Cytogenetic Alterations
MONOSOMY_13 = 'monosomy_chr_13'
MONOSOMY_14 = 'monosomy_chr_14'
MONOSOMY_17 = 'monosomy_chr_17'
DEL_1P = 'chr_1p_deletion'
DEL_17P = 'chr_17p_deletion'
AMP_1P = 'chr_1p_gain_or_amp'
AMP_1Q = 'chr_1q_gain_or_amp'
HYPERDIPLOIDY = 'hyperdiploidy'
BI_DEL_1P32 = 'biallelic_deletion_1p32'
MONO_DEL_1P32 = 'monoallelic_deletion_1p32'
CYTOGEN_ALTS = 'cytogenetic_alterations'

# High risk
HIGH_RISK = "high_risk_myeloma"

# APOBEC gene signatures
APOBEC_SIGS = 'apobec_gene_signatures'
SBS2 = 'SBS2'
SBS13 = 'SBS13'
# Need to find in provenance since Djerba doesn't write it to the workspace:
SBS_JSON = '.exposures.SBS.json'
SBS_FILE = 'hrdetect_sbs_file'
SBS_WORKFLOW = 'hrDetect_sbs'

# TP53 alteration
P53_ALT = "p53_SNV_or_CNV"

# Parameter names
DATA_MUTATIONS_FILE = 'mutations_file'
DATA_CNA_FILE = 'cna_file'
DATA_EXPRESSION_FILE = 'expression_file'
PURPLE_SEGMENTS_FILE = 'purple.segments.txt'
PURPLE_CNV_GENE_FILE = 'purple_cnv_gene_file'
PURITY_PLOIDY_JSON = 'purity_ploidy.json'
TRANSLOCATION_FILE = 'translocation_file'

# File names
DATA_MUTATIONS_TXT = 'data_mutations_extended.txt'
#DATA_CNA_TXT = 'purple.data_CNA.txt'
DATA_EXPRESSION_TXT = 'data_expression_percentile_tcga.txt'

# List of MM genes

GENES = ["TP53", "MYC", "NRAS", "KRAS", "CDKN2C", "NFKB1", "NFKB2", "RB1", "BRAF", "CDK6", "ATM", "TNFRSF17", "CD38", "CRBN", "FCRH5", "FGFR3", "GPRC5D", "CKS1B"] 

# List of MM translocations
TRANSLOCATIONS = 'ig_translocations'
HIGH_RISK_TRANSLOC = 'high_risk_translocations'
IGH = 'IGH' 
t4_14 = 't(4;14)'
t14_16 = 't(14;16)'
t14_20 = 't(14;20)'
t8_14 = 't(8;14)'
t11_14 = 't(11;14)'
t6_14 = 't(6;14)'
IGK = 'IGK'
t2_8 = 't(2;8)'
IGL = 'IGL'
t8_22 = 't(8;22)'



# For extract
MUTATION_TYPE = 'Mutation Type'
MUTATION_ALT = 'Mutation Alteration'
MUTATION_FOUND = 'Mutation Found'
COPY_NUMBER = 'Copy Number'
EXPRESSION_PERCENTILE = 'Expression Percentile'
CHECKMARK = 'Matches Criteria'
