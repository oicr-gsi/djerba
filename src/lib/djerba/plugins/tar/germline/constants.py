"""
Germline variants are called with EfficientDV and annotated with VEP, then
restricted to the Hereditary Cancer Comprehensive Panel and annotated with
OncoKB for oncogenicity. See JIRA GBS-7157.
"""

### INI config keys ###

DONOR = 'donor'
ONCOTREE = 'oncotree_code'
TUMOUR_ID = 'tumour_id'
GERMLINE_MAF_FILE = 'germline_maf_file'

### Workspace layout ###
# Created a germline subdir under the work dir to store all germline intermediate files to avoid conflicts with
# somatic outputs.
GERMLINE_SUBDIR = 'germline'
PANEL_GENES_ONLY = 'panel_genes_only.tsv'
FILTERED_MAF = 'filtered_maf.tsv'
GERMLINE_ALL = 'germline_variants_all.txt'
GERMLINE_ONCOGENIC = 'germline_variants_oncogenic.txt'

### MAF column names ###
CHROMOSOME_COL = 'Chromosome'
CLIN_SIG = 'CLIN_SIG'
END_POSITION = 'End_Position'
FILTER = 'FILTER'
HGVSC = 'HGVSc'
HGVSP_SHORT = 'HGVSp_Short'
HUGO_SYMBOL = 'Hugo_Symbol'
MATCHED_NORM_SAMPLE_BARCODE = 'Matched_Norm_Sample_Barcode'
N_ALT_COUNT = 'n_alt_count'
N_DEPTH = 'n_depth'
NCBI_BUILD = 'NCBI_Build'
REFERENCE_ALLELE = 'Reference_Allele'
START_POSITION = 'Start_Position'
SYMBOL = 'SYMBOL'
T_ALT_COUNT = 't_alt_count'
T_DEPTH = 't_depth'
TUMOUR_SAMPLE_BARCODE = 'Tumor_Sample_Barcode'
TUMOUR_SEQ_ALLELE2 = 'Tumor_Seq_Allele2'
VARIANT_CLASSIFICATION = 'Variant_Classification'

MAF_REQUIRED_KEYS = [
    CHROMOSOME_COL,
    CLIN_SIG,
    END_POSITION,
    FILTER,
    HGVSC,
    HGVSP_SHORT,
    HUGO_SYMBOL,
    NCBI_BUILD,
    REFERENCE_ALLELE,
    START_POSITION,
    T_ALT_COUNT,
    T_DEPTH,
    TUMOUR_SAMPLE_BARCODE,
    TUMOUR_SEQ_ALLELE2,
    VARIANT_CLASSIFICATION,
]

# Derived columns written by preprocess
TUMOUR_VAF = 'tumour_vaf'
CLIN_SIG_DISPLAY = 'clin_sig_display'

### Filtering ###
# Germline heterozygous variants are expected near VAF 0.5 and homozygous variants near 1.0.
# A 0.20 VAF floor removes low-level artifacts and somatic/clonal hematopoiesis variants while
# retaining typical germline calls.
MIN_VAF_GERMLINE = 0.20

# Minimum read depth for a callable position.
MIN_DEPTH = 10

# This list keeps variants more likely to have a clinically meaningful effect on the protein or splicing.
# A ClinVar-pathogenic call overrides this list entirely.
GERMLINE_MUTATION_TYPES = [
    'Frame_Shift_Del',
    'Frame_Shift_Ins',
    'In_Frame_Del',
    'In_Frame_Ins',
    'Missense_Mutation',
    'Nonsense_Mutation',
    'Nonstop_Mutation',
    'Splice_Region',
    'Splice_Site',
    'Translation_Start_Site',
]

# Keep variants with FILTER = PASS or where no filter was specified (. or '').
FILTER_PASS_VALUES = ['PASS', '.', '']

# ClinVar significance terms that force a variant to be reported regardless of
# consequence, so a deep-intronic or UTR pathogenic allele is never dropped.
CLIN_SIG_PATHOGENIC = ['pathogenic', 'likely_pathogenic']

### Results keys ###
TOTAL_GERMLINE_VARIANTS = 'Total germline variants'
REPORTABLE_GERMLINE_VARIANTS = 'Reportable germline variants'
VUS_GERMLINE_VARIANTS = 'Germline variants of uncertain significance'
PANEL_GENE_COUNT = 'Panel gene count'
BODY = 'Body'
VUS_BODY = 'VUS body'

### Render keys ###
GENE = 'Gene'
GENE_URL = 'Gene_URL'
CHROMOSOME = 'Chromosome'
PROTEIN = 'Protein'
PROTEIN_URL = 'Protein_URL'
MUTATION_TYPE = 'Type'
VAF_PERCENT = 'VAF (%)'
VAF_NOPERCENT = 'VAF'
DEPTH = 'Depth'
TUMOUR_DEPTH = 't_depth'
TUMOUR_ALT_COUNT = 't_alt_count'
CLIN_SIG_DISPLAY_KEY = 'ClinVar'

ONCOKB = 'OncoKB level'

# Appended to the alteration in treatment_options_merger entries.
# The merger deduplicates on (OncoKB level, Alteration, Gene), so this makes sure a germline or somatic hit
# on the same variant doesn't collapse into one row.
GERMLINE_TAG = ' (germline)'

### Hereditary Cancer Comprehensive Panel ###
PANEL_GENE_SOURCE = 'Hereditary Cancer Comprehensive Panel (GBS-7157, 2026-07)'

PANEL_GENES = frozenset([
    'AIP', 'APC', 'ATM', 'AXIN2', 'BAP1', 'BARD1', 'BMPR1A', 'BRCA1', 'BRCA2',
    'BRIP1', 'CDC73', 'CDH1', 'CDK4', 'CDKN1B', 'CDKN2A', 'CHEK2', 'CTNNA1',
    'DICER1', 'EGFR', 'EGLN1', 'EPCAM', 'EXT1', 'EXT2', 'FH', 'FLCN',
    'GALNT12', 'GREM1', 'HOXB13', 'KIT', 'LZTR1', 'MAX', 'MEN1', 'MET', 'MITF',
    'MLH1', 'MLH3', 'MSH2', 'MSH3', 'MSH6', 'MUTYH', 'NBN', 'NF1', 'NF2',
    'NTHL1', 'PALB2', 'PDGFRA', 'PMS2', 'POLD1', 'POLE', 'POT1', 'PRKAR1A',
    'PTCH1', 'PTEN', 'RAD51C', 'RAD51D', 'RB1', 'RECQL', 'RET', 'RNF43',
    'RPS20', 'SDHA', 'SDHAF2', 'SDHB', 'SDHC', 'SDHD', 'SMAD4', 'SMARCA4',
    'SMARCB1', 'SMARCE1', 'STK11', 'SUFU', 'TMEM127', 'TP53', 'TSC1', 'TSC2',
    'VHL',
])
PANEL_GENE_TOTAL = 76

# Fail at import rather than silently under-reporting if the list is edited.
assert len(PANEL_GENES) == PANEL_GENE_TOTAL, \
    'Expected {0} panel genes, found {1}'.format(PANEL_GENE_TOTAL, len(PANEL_GENES))
