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
VCF_FILE = 'vcf_file'
VIRUS_FILE = 'virus_file'
REPORT_DIR = 'report_dir'

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
SWISNF_GENES = ['SMARCB1', 'SMARCA4', 'ARID1A', 'ARID1B', 'PBRM1']
SPECIES = 'name_species'
BED_FILE_NAME = '/gencode.v31.ensg_annotation_w_entrez.bed'

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

# Name for output file
CAPTIV8_INPUT = 'captiv8_input.txt'
CAPTIV8_OUTPUT = 'captiv8_output.txt'

