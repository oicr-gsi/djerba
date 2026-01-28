"""
Constants for the Genomic Landscape plugin.
"""

# Constants for configure
ONCOTREE_CODE = 'oncotree_code'
TUMOUR_ID = 'tumour_id'
TCGA_CODE = 'tcga_code'
PURITY_INPUT = 'purity'
DONOR = 'donor'
MSI_FILE = 'msi_file'
CTDNA_FILE = 'ctdna_file'
SAMPLE_TYPE = 'sample_type'
UNKNOWN_SAMPLE_TYPE = 'Unknown sample type'
COVERAGE_MEAN = 'coverage'

# Constants for render
PURITY_REASON = 'purity'
COVERAGE_REASON = 'coverage'
AVAILABILITY_REASON = 'hrd_unavailable'

# biomarker reportability
CAN_REPORT_HRD = 'can_report_hrd'
CAN_REPORT_MSI = 'can_report_msi'
CANT_REPORT_HRD_REASON = 'cant_report_hrd_reason'

# For MSI file
MSI_RESULTS_SUFFIX = '.recalibrated.msi.booted'
MSI_WORKFLOW = 'msisensor'

# For ctDNA file
CTDNA_RESULTS_SUFFIX = 'SNP.count.txt'
CTDNA_WORKFLOW = 'mrdetect_filter_only'

HRD_WORKFLOW = 'hrDetect'

# Constants for the rest of the plugin in alphabetical order
ALT = 'Alteration'
ALT_URL = 'Alteration_URL'
ALTERATION_UPPER_CASE = 'ALTERATION'
BIOMARKERS = 'genomic_biomarkers'
BODY = 'Body'
CANCER_SPECIFIC_PERCENTILE = 'Cancer-specific Percentile'
CANCER_SPECIFIC_COHORT = 'Cancer-specific Cohort'
CANCER_TYPE_HEADER = 'CANCER.TYPE'
CLINICALLY_RELEVANT_VARIANTS = 'Clinically relevant variants'
COMPASS = 'COMPASS'
CTDNA = 'ctDNA'
CTDNA_CANDIDATES = 'ctDNA_candidate_sites'
CTDNA_ELIGIBILITY = 'ctDNA_eligibility'
CTDNA_ELIGIBILITY_CUTOFF = 4000
DATA_SEGMENTS = 'data.seg'
GENOME_SIZE = 3*10**9 # TODO use more accurate value when we release a new report format
GENOMIC_BIOMARKERS = 'genomic_biomarkers.maf'
GENOMIC_BIOMARKERS_ANNOTATED = 'genomic_biomarkers_annotated.maf'
GENOMIC_LANDSCAPE_INFO = 'genomic_landscape_info'
HUGO_SYMBOL = "Other Biomarkers"
METRIC_ACTIONABLE = 'Genomic alteration actionable'
METRIC_ALTERATION = 'Genomic biomarker alteration'
METRIC_PLOT = 'Genomic biomarker plot'
METRIC_TEXT = 'Genomic biomarker text'
METRIC_VALUE = 'Genomic biomarker value'
MINIMUM_MAGNITUDE_SEG_MEAN = 0.2
MRDETECT_FILTER_ONLY_FILE_NAME = 'SNP.count.txt'
MSI = "MSI"
MSI_CUTOFF = 15.0
MSI_FILE_NAME = 'msi.txt'
MSS_CUTOFF = 5.0
MUTATIONS_EXTENDED = 'data_mutations_extended.txt'
NA = 'NA'
ONCOKB = 'OncoKB'
PAN_CANCER_COHORT = 'Pan-cancer Cohort'
PAN_CANCER_COHORT_VALUE = 'TCGA Pan-Cancer Atlas 2018 (n=6,446)'
PAN_CANCER_PERCENTILE = 'Pan-cancer Percentile'
PERCENT_GENOME_ALTERED = 'Percent Genome Altered'
PROVENANCE_OUTPUT = 'provenance_subset.tsv.gz'
PURITY = 'Estimated Cancer Cell Content (%)'
TMB = "TMB"
TMB_EXCLUDED = [
    "3'Flank",
    "3'UTR",
    "5'Flank",
    "5'UTR",
    "Silent",
    "Splice_Region",
    "Targeted_Region",
    ]
TMBCOMP_EXTERNAL = 'tmbcomp-externaldata.txt'
TMB_HEADER = 'tmb'
TMB_PER_MB = 'TMB per megabase'
TMBCOMP_TCGA = 'tmbcomp-tcga.txt'
TMB_TOTAL = 'Tumour Mutation Burden'
TREATMENT = 'Treatment'
VARIANT_CLASSIFICATION = 'Variant_Classification'
V7_TARGET_SIZE = 37.285536 # inherited from CGI-Tools

HRD = 'HRD'
HRD_short = 'HRD_short'
HRD_long = 'HRD_long'
HRD_PLOT = 'hrd_base64'
HRDETECT_PATH = 'hrd_path'
