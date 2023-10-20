"""
CONSTANTS
"""

# broad
#DATA_DIR_NAME = 'data'

# sequenza
#SEQUENZA_GAMMA = 'sequenza_gamma'

# extract constants for oncokb
#AUTHOR = 'author'
#ASSAY_TYPE = 'assay_type'
#COVERAGE = 'coverage'
#FAILED = 'failed'
#ONCOKB_CACHE = 'oncokb_cache'
#ONCOTREE_CODE = 'oncotree_code'
#PURITY_FAILURE = 'purity_failure'
#PROJECT = 'Project'

# clinical data file headers
#TUMOUR_SAMPLE_ID = 'TUMOUR_SAMPLE_ID'
#CLINICAL_DATA_FILENAME = 'data_clinical.txt'
#CLOSEST_TCGA = 'CLOSEST_TCGA'

# constants for other biomarkers

MSI = "MSI"
TMB = "TMB"
ALT = 'Alteration'
ALT_URL = 'Alteration_URL'
METRIC_VALUE = 'Genomic biomarker value'
METRIC_ACTIONABLE = 'Genomic alteration actionable'
METRIC_ALTERATION = 'Genomic biomarker alteration'
METRIC_TEXT = 'Genomic biomarker text'
METRIC_PLOT = 'Genomic biomarker plot'
HUGO_SYMBOL = "Other Biomarkers"
#METRIC_CALL = 'Genomic biomarker call'
GENOMIC_LANDSCAPE_INFO = 'genomic_landscape_info'
BIOMARKERS = 'genomic_biomarkers'

# render constants for the genomic landscape table
TMB_TOTAL = 'Tumour Mutation Burden'
TMB_PER_MB = 'TMB per megabase'
PERCENT_GENOME_ALTERED = 'Percent Genome Altered'
CANCER_SPECIFIC_PERCENTILE = 'Cancer-specific Percentile'
CANCER_SPECIFIC_COHORT = 'Cancer-specific Cohort'
PAN_CANCER_PERCENTILE = 'Pan-cancer Percentile'
PAN_CANCER_COHORT = 'Pan-cancer Cohort'
CLINICALLY_RELEVANT_VARIANTS = 'Clinically relevant variants'
BODY = 'Body'

GENOMIC_BIOMARKERS = 'genomic_biomarkers.maf'
GENOMIC_BIOMARKERS_ANNOTATED = 'genomic_biomarkers_annotated.maf'

TMB_HEADER = 'tmb' # for tmbcomp files
CANCER_TYPE_HEADER = 'CANCER.TYPE' # for tmbcomp files
TMBCOMP_EXTERNAL = 'tmbcomp-externaldata.txt'
TMBCOMP_TCGA = 'tmbcomp-tcga.txt'

MUTATIONS_EXTENDED = 'data_mutations_extended.txt'
VARIANT_CLASSIFICATION = 'Variant_Classification'
    
TMB_EXCLUDED = [
    "3'Flank",
    "3'UTR",
    "5'Flank",
    "5'UTR",
    "Silent",
    "Splice_Region",
    "Targeted_Region",
    ]

V7_TARGET_SIZE = 37.285536 # inherited from CGI-Tools
NA = 'NA'
COMPASS = 'COMPASS'

DATA_SEGMENTS = 'data_seg.txt'
MINIMUM_MAGNITUDE_SEG_MEAN = 0.2
GENOME_SIZE = 3*10**9 # TODO use more accurate value when we release a new report format

#PURITY_PERCENT = 'Estimated Cancer Cell Content (%)'
