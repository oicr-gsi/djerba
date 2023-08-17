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

## Preprocess Constants


GEP_GENE_ID_INDEX = 0
GEP_FPKM_INDEX = 6

# MAF filter thresholds
MIN_VAF = 0.1
MIN_VAF_TAR = 0.01
MAX_UNMATCHED_GNOMAD_AF = 0.001

WHIZBAM_BASE_URL = 'https://whizbam.oicr.on.ca'
gep_reference = "/.mounts/labs/CGI/gsi/tools/djerba/gep_reference.txt.gz"
ONCOLIST =  "/data/20200818-oncoKBcancerGeneList.tsv"
ENSEMBL_CONVERSION =  "data/ensemble_conversion_hg38.txt"
TCGA_RODIC = "/.mounts/labs/CGI/gsi/tools/RODiC/data"
CYTOBAND = "/data/cytoBand.txt"

# headers of important MAF columns
VARIANT_CLASSIFICATION = 'Variant_Classification'
TUMOUR_SAMPLE_BARCODE = 'Tumor_Sample_Barcode'
MATCHED_NORM_SAMPLE_BARCODE = 'Matched_Norm_Sample_Barcode'
FILTER = 'FILTER'
T_DEPTH = 't_depth'
GNOMAD_AF = 'gnomAD_AF'
MAF_KEYS = [
    VARIANT_CLASSIFICATION,
    TUMOUR_SAMPLE_BARCODE,
    MATCHED_NORM_SAMPLE_BARCODE,
    FILTER,
    T_DEPTH,
    TUMOUR_ALT_COUNT,
    GNOMAD_AF
]

# Permitted MAF mutation types
# `Splice_Region` is *included* here, but *excluded* from the somatic mutation count used to compute TMB in report_to_json.py
# See also JIRA ticket GCGI-469
MUTATION_TYPES_EXONIC = [
    "3'Flank",
    "3'UTR",
    "5'Flank",
    "5'UTR",
    "Frame_Shift_Del",
    "Frame_Shift_Ins",
    "In_Frame_Del",
    "In_Frame_Ins",
    "Missense_Mutation",
    "Nonsense_Mutation",
    "Nonstop_Mutation",
    "Silent",
    "Splice_Region",
    "Splice_Site",
    "Targeted_Region",
    "Translation_Start_Site"
]

# disallowed MAF filter flags; from filter_flags.exclude in CGI-Tools
FILTER_FLAGS_EXCLUDE = [
    'str_contraction',
    't_lod_fstar'
]

COPY_STATE_CONVERSION = {
    0: "Neutral",
    1: "Gain",
    2: "Amplification",
    -1: "Shallow Deletion",
    -2: "Deep Deletion"
}
