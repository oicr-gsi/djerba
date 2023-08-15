"""
This file contains a list of constants to be used in the TAR SNV Indel plugin.
"""

# For rendering
TOTAL_VARIANTS = 'Total variants'
CLINICALLY_RELEVANT_VARIANTS = 'Clinically relevant variants'
BODY = 'Body'
HAS_EXPRESSION_DATA = 'Has expression data'
EXPRESSION_METRIC = 'Expression Percentile'
GENE = 'Gene'
GENE_URL = 'Gene_URL'
CHROMOSOME = 'Chromosome'
DEPTH = 'Depth'
ALTERATION = 'Alteration'
ONCOKB = 'OncoKB'
CNV_PLOT = 'cnv_plot'
TEXT_ENCODING = 'utf-8'
PROTEIN = 'Protein'
PROTEIN_URL = 'Protein_URL'
MUTATION_TYPE = 'Type'
VAF_PERCENT = 'VAP (%)'
VAF_NOPERCENT = 'VAF'
TUMOUR_DEPTH = 't_depth'
TUMOUR_ALT_COUNT = 't_alt_count'
COPY_STATE = 'Copy State'
LOH_STATE = 'LOH (ABratio)'
ONCOKB = 'OncoKB'
VAF_PLOT = 'vaf_plot'
TMB_TOTAL = 'Tumour Mutation Burden'

# EXTRACT CONSTANTS
ALTERATION_UPPER_CASE = 'ALTERATION'
ONCOGENIC = 'ONCOGENIC'
CNA_SIMPLE = 'data_CNA.txt'
CNA_ANNOTATED = "data_CNA_oncoKBgenes_nonDiploid_annotated.txt"
EXPR_PCT_TCGA = 'data_expression_percentile_tcga.txt'
HGVSC = 'HGVSc'
HGVSP_SHORT = 'HGVSp_Short'
HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
HUGO_SYMBOL_TITLE_CASE = 'Hugo_Symbol'
MUTATIONS_EXTENDED = 'data_mutations_extended.txt'
MUTATIONS_EXTENDED_ONCOGENIC = 'data_mutations_extended_oncogenic.txt'
NA = 'NA'
ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
TUMOUR_VAF = 'tumour_vaf'
UNKNOWN = 'Unknown'
VARIANT_CLASSIFICATION = 'Variant_Classification'

UNCLASSIFIED_CYTOBANDS = [
"", # some genes have an empty string for cytoband
"mitochondria",
"not on reference assembly",
"reserved",
"unplaced",
"13cen",
"13cen, GRCh38 novel patch",
"2cen-q11",
"2cen-q13",
"c10_B",
"HSCHR6_MHC_COXp21.32",
"HSCHR6_MHC_COXp21.33",
"HSCHR6_MHC_COXp22.1",
"Unknown"
]
