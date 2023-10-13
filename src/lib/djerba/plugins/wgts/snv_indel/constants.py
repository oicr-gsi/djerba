ONCOTREE_CODE = 'oncotree_code'
CBIO_ID = 'cbio_id'
TUMOUR_ID = 'tumour_id'
NORMAL_ID = 'normal_id'
MAF_PATH = 'maf_path'
CNA_PATH = 'cna_path'

# important MAF headers
VARIANT_CLASSIFICATION = 'Variant_Classification'
TUMOUR_SAMPLE_BARCODE = 'Tumor_Sample_Barcode'
MATCHED_NORM_SAMPLE_BARCODE = 'Matched_Norm_Sample_Barcode'
FILTER = 'FILTER'
T_DEPTH = 't_depth'
T_ALT_COUNT = 't_alt_count'
GNOMAD_AF = 'gnomAD_AF'
HUGO_SYMBOL = 'Hugo_Symbol'
MAF_KEYS = [
    VARIANT_CLASSIFICATION,
    TUMOUR_SAMPLE_BARCODE,
    MATCHED_NORM_SAMPLE_BARCODE,
    FILTER,
    T_DEPTH,
    T_ALT_COUNT,
    GNOMAD_AF,
    HUGO_SYMBOL
]
HGVSP_SHORT = 'HGVSp_Short'

# Permitted MAF mutation types
# `Splice_Region` is *included* here, but *excluded* from TMB computation
# See also JIRA ticket GCGI-469
MUTATION_TYPES_EXONIC = [
    "5'Flank",
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

# variant classifications excluded from TMB count
TMB_EXCLUDED = [
    "3'Flank",
    "3'UTR",
    "5'Flank",
    "5'UTR",
    "Silent",
    "Splice_Region",
    "Targeted_Region",
]


# MAF filter thresholds
MIN_VAF = 0.1
MAX_UNMATCHED_GNOMAD_AF = 0.001

# filenames
VAF_PLOT = 'vaf_plot.svg'
WHIZBAM_ALL = 'whizbam_all.txt'
WHIZBAM_ONCOGENIC = 'whizbam_oncogenic.txt'
MUTATIONS_ALL = 'data_mutations_extended.txt'
MUTATIONS_ONCOGENIC = 'data_mutations_extended_oncogenic.txt'
WHIZBAM_TEMPLATE = 'whizbam_template.html'

# output keys
TYPE = 'type'
VAF = 'vaf'
VAF_PLOT = 'vaf_plot'
DEPTH = 'depth'
COPY_STATE = 'copy state'
SOMATIC_MUTATIONS = 'somatic mutations'
CODING_SEQUENCE_MUTATIONS = 'coding sequence mutations'
ONCOGENIC_MUTATIONS = 'oncogenic mutations'
