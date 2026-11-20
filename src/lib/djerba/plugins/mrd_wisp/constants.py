#assay settings
DETECTION_ALPHA = 0.01 # as defined by WISP 

# table constants
COHORT_N = 'hbc_n'
COVERAGE = 'coverage'
CTDNA_DETECTION = 'ctdna_detection'
CTDNA_OUTCOME = 'outcome'
DETECTION_PLOT = 'detection_plot'
INSERT_SIZE = 'median_insert_size'
PVALUE = 'p-value'  
RESULTS = 'results' 
SIGNIFICANCE = 'significance_text'       
SNV_COUNT = 'candidate_snv_count' # need to re-examine for WISP

# sample constants
ASSAY = 'assay'
DONOR = 'donor'
GROUP_ID = 'group_id'
PATIENT_ID = 'Patient Study ID'
PATIENT_ID_LOWER = 'patient_study_id'
PRIMARY_CANCER = 'primary_cancer'
PROJECT = 'project'
PROVENANCE_ID = 'provenance_id'
PWGS_REPORT = 'pwgs_report_id'
REQ_APPROVED = 'requisition_approved'
REQ_ID = 'requisition_id'
STUDY = 'study'
WGS_REPORT = 'wgs_report_id'

# file constants
BAMQC = 'bamqc_results'
PROVENANCE_OUTPUT = 'provenance_subset.tsv.gz'
#PWGS_PLOT = 'pwgs_base64'
RESULTS_FILE = 'results_file' 
ALL_TIMEPOINTS_DIR = 'all_timepoints_dir'
SNV_COUNT_FILE = 'primary_snv_count_file'
WGS_JSON = 'wgs_json'
#VAF_FILE = 'vaf_file'
CARDEA_URL = 'cardea_url'
QCETL_CACHE = 'qcetl_cache'
DETECTION_PLOT = 'detection_plot.png'
MRD_CALL_FILE = 'mrd_call.txt' 

# extract constants
MRD_CALL = 'mrd_call' 
NAME = 'name' 
STATUS = 'status'
SNV_LOD = 'snv_lod'
TF = 'tumour_fraction'
CANDIDATE_SITES = 'candidate_sites_passing_qc' 
TOTAL_FRAGMENTS = 'total_fragments' 
ALLELE_FRAGMENTS = 'allele_fragments' 


# WISP table headers
WISP_AF = "AlleleFragments"
WISP_TF = "SNVPurity"
WISP_DETECTION = "SNV_MRD"
WISP_TABLE_DATA = "wisp_table_data"

# timepoints
TIMEPOINT = 'timepoint'

# file extensions
RESULTS_SUFFIX = '\.wisp_summary\.txt$' 
BAMQC_SUFFIX = 'bamQC_results.json'
SNV_COUNT_SUFFIX = 'SNP.count.txt'

# render constants
ANALYSIS_TEMPLATE_NAME = 'analysis_template.html'
SAMPLE_TEMPLATE_NAME = 'sample_template.html'
SUMMARY_TEMPLATE_NAME = 'summary_template.html' 
CASE_OVERVIEW_TEMPLATE_NAME = 'case_template.html'
