"""
Constants for the CAPTIV-8 plugin
"""
CAPTIV8_PLOT = 'captiv8_base64'
ELIGIBILITY = 'eligibility'
SCORE = 'captiv8-score'

# Required parameter names for INI
DONOR = 'donor'
TUMOUR_ID = 'tumour_id'
ONCOTREE_CODE = 'oncotree_code'
PRIMARY_CANCER = 'primary_cancer'
IS_HEME = 'is_hemeotological_cancer' # defaults to false
SITE_OF_BIOPSY = 'site_of_biopsy'
RSEM_FILE = 'rsem_file'
CIBERSORT_FILE = 'cibersort_file'
MAF_FILE = 'maf_file'
VIRUS_FILE = 'virus_file'
REPORT_DIR = 'report_dir'

# File workflow names and suffixes
VIRUS_WORKFLOW = 'virusbreakend'
VIRUS_SUFFIX = '.vcf.summary.tsv'
MAF_WORKFLOW = 'variantEffectPredictor_matched'
MAF_SUFFIX = '.mutect2.filtered.maf.gz$'
RSEM_WORKFLOW = 'rsem'
RSEM_SUFFIX = '.genes.results'
CIBERSORT_WORKFLOW = 'immunedeconv'
CIBERSORT_SUFFIX = '.immunedeconv_CIBERSORT-Percentiles.csv'

# Misc Constants
COLREC_ONCOTREE_CODES = ["COADREAD", "COAD", "CAIS", "MACR", "READ", "SRCCR"]
# Driver viruses from: https://github.com/hartwigmedical/hmftools/blob/master/virus-interpreter/src/test/resources/virus_interpreter/real_virus_reporting_db.tsv
DRIVER_VIRUSES = ["Human gammaherpesvirus 4",
                    "Hepatitis B virus",
                    "Human gammaherpesvirus 8",
                    "Alphapapillomavirus 11",
                    "Alphapapillomavirus 5",
                    "Alphapapillomavirus 6",
                    "Alphapapillomavirus 7",
                    "Alphapapillomavirus 9",
                    "Alphapapillomavirus 1",
                    "Alphapapillomavirus 10",
                    "Alphapapillomavirus 13",
                    "Alphapapillomavirus 3",
                    "Alphapapillomavirus 8",
                    "Human polyomavirus 5"]
SWISNF_GENES = ['SMARCB1', 'SMARCA4', 'ARID1A', 'ARID1B', 'PBRM1', 'ARID2']
SPECIES = 'name_species'
BED_FILE_NAME = 'gencode.v31.ensg_annotation_w_entrez.bed'
TMB_EXCLUDED = [
    "3'Flank",
    "3'UTR",
    "5'Flank",
    "5'UTR",
    "Silent",
    "Splice_Region",
    "Targeted_Region",
    ]

# Output constants
PATIENT = 'patient'
ID = 'lib'
CIBERSORT_PATH = 'cibersort'
RSEM_PATH = 'rsem'
TMB_VALUE = 'tmbur'
SWI_SNF = 'swisnf'
COLORECTAL = 'colorectal'
LYMPH = 'lymph'
VIRUS = 'virus'

DATA_MUTATIONS_EXTENDED = 'data_mutations_extended.txt'
DATA_CNA = 'data_CNA.txt'
TUMOUR_VAF = 'tumour_vaf'
VAF_CUTOFF = 0.1
DIVISOR = 3095.978588 # cat $HG38_ROOT/hg38_random.fa | grep -v "^>" | sed s:[^ACGTacgt]::g | tr -d  "\n" | wc -m

# For maf table
T_DEPTH = 't_depth'
T_ALT_COUNT = 't_alt_count'

# Name for output file
CAPTIV8_INPUT = 'captiv8_input.txt'
CAPTIV8_OUTPUT = 'captiv8_output.txt'

