#assay settings
DETECTION_ALPHA = 0.01 # as defined by WISP 

# table constants
COHORT_N = 'hbc_n'
COVERAGE = 'coverage'
CTDNA_DETECTION = 'ctdna_detection'
CTDNA_OUTCOME = 'outcome'
#DATASET_DETECTION_CUTOFF = 'dataset_detection_cutoff'
DETECTION_PLOT = 'detection_plot'
INSERT_SIZE = 'median_insert_size'
PVALUE = 'p-value'  
#READS_CHECKED = 'reads_checked'
#READS_DETECTED = 'reads_detected'
RESULTS = 'results' 
SIGNIFICANCE = 'significance_text'       
#SITES_CHECKED = 'sites_checked'
#SITES_DETECTED = 'sites_detected'
SNV_COUNT = 'candidate_snv_count' # need to re-examine for WISP
#TUMOUR_FRACTION_ZVIRAN = 'TFZ'            
#TUMOUR_FRACTION_READS = 'TFR'            

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
SNV_COUNT_FILE = 'primary_snv_count_file'
WGS_JSON = 'wgs_json'
#VAF_FILE = 'vaf_file'
CARDEA_URL = 'cardea_url'
QCETL_CACHE = 'qcetl_cache'
DETECTION_PLOT = 'detection_plot.png'
MRD_CALL_FILE = 'mrd_call.txt' 

# extract constants
MRD_CALL = 'mrd_call' 
ALL_SITES_DETECTED = 'all_sites_detected'
HBC_SITES_DETECTED = 'hbc_detected_sites' 
NAME = 'name' 
STATUS = 'status'
TUMOUR_SITES_DETECTED = 'tumour_sites_detected' 
CANDIDATE_SITES = 'candidate_sites_passing_qc' 
READS_DETECTED = 'reads_detected' 
READS_CHECKED = 'reads_checked' 
READ_PERCENTAGE = 'read_percentage' 
DETECTION_CUTOFF = 'detection_cutoff_sites' 



# file extensions
RESULTS_SUFFIX = '\.wisp_summary\.txt$' 
BAMQC_SUFFIX = 'bamQC_results.json'
SNV_COUNT_SUFFIX = 'SNP.count.txt'

# render constants
ANALYSIS_TEMPLATE_NAME = 'analysis_template.html'
SAMPLE_TEMPLATE_NAME = 'sample_template.html'
SUMMARY_TEMPLATE_NAME = 'summary_template.html' 
CASE_OVERVIEW_TEMPLATE_NAME = 'case_template.html'
