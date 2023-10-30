ONCOTREE_CODE = 'oncotree code'
STUDY_ID = 'study_id' # cbioportal study ID, eg. PASS01
TUMOUR_ID = 'tumour_id'
NORMAL_ID = 'normal_id'
MAF_PATH = 'maf_path'
CNA_PATH = 'cna_path'
HAS_EXPRESSION_DATA = 'has expression data'

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
HGVSC = 'HGVSc'

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
VAF_PLOT_FILENAME = 'vaf_plot.svg'
WHIZBAM_ALL = 'whizbam_all.txt'
WHIZBAM_ONCOGENIC = 'whizbam_oncogenic.txt'
MUTATIONS_ALL = 'data_mutations_extended.txt'
MUTATIONS_ONCOGENIC = 'data_mutations_extended_oncogenic.txt'
WHIZBAM_TEMPLATE = 'whizbam_template.html'
ENSEMBL_CONVERSION = 'ensemble_conversion_hg38.txt'

# output keys
TYPE = 'type'
VAF = 'vaf'
VAF_PLOT = 'vaf_plot'
DEPTH = 'depth'
PROTEIN = 'protein'
PROTEIN_URL = 'protein_url'
COPY_STATE = 'copy state'
SOMATIC_MUTATIONS = 'somatic mutations'
CODING_SEQUENCE_MUTATIONS = 'coding sequence mutations'
ONCOGENIC_MUTATIONS = 'oncogenic mutations'

# misc
WHIZBAM_BASE_URL = 'https://whizbam.oicr.on.ca'

# HTML headers
VAF_UC = 'VAF'

EXPRESSION_METRIC = 'Expression Percentile'
GENE = 'Gene'
GENE_URL = 'Gene_URL'
HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
ALT = 'Alteration'
ALT_URL = 'Alteration_URL'
ALTERATION_UPPER_CASE = 'ALTERATION'
CHROMOSOME = 'Chromosome'
GENOME_SIZE = 3*10**9 # TODO use more accurate value when we release a new report format
MINIMUM_MAGNITUDE_SEG_MEAN = 0.2
GENEBED =  "data/gencode_v33_hg38_genes.bed"
ONCOLIST =  "data/20200818-oncoKBcancerGeneList.tsv"
CENTROMERES = "data/hg38_centromeres.txt"
ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
CYTOBAND = "/data/cytoBand.txt"
HUGO_SYMBOL_TITLE_CASE = 'Hugo_Symbol'
MUTATION_TYPE = 'Type'
VAF_PERCENT = 'VAP (%)'


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
NA = 'NA'
ONCOGENIC = 'ONCOGENIC'

TOTAL_VARIANTS = 'Total variants'
CLINICALLY_RELEVANT_VARIANTS = 'Clinically relevant variants'
BODY = 'Body'
PERCENT_GENOME_ALTERED = 'Percent Genome Altered'
ALTERATION = 'Alteration'
ONCOKB = 'OncoKB'
HAS_EXPRESSION_DATA = 'Has expression data'
