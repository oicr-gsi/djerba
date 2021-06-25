"""Field names for the input INI file"""

# section names
INPUTS = 'inputs'
SEG = 'seg'
SETTINGS = 'settings'
DISCOVERED = 'discovered'
SAMPLE_META = 'sample_meta'

# parameter names
AMPL = 'ampl'
BED_PATH = 'bed_path'
CANCER_TYPE = 'cancer_type'
CANCER_TYPE_DESCRIPTION = 'cancer_type_description'
CANCER_TYPE_DETAILED = 'cancer_type_detailed'
DATA_DIR = 'data_dir'
DATE_SAMPLE_RECEIVED = 'date_sample_received'
ENSCON = 'enscon'
ENTCON = 'entcon'
FUS_FILE = 'fusfile'
GAIN = 'gain'
GAMMA = 'gamma'
GENE_BED = 'genebed'
GENE_LIST = 'genelist'
GEP_FILE = 'gepfile'
GEP_REFERENCE = 'gep_reference'
HTZD = 'htzd'
HMZD = 'hmzd'
MAF_FILE = 'maf_file'
MEAN_COVERAGE = 'mean_coverage'
METRICS_FILENAME = 'metrics_filename'
METRICS_SCHEMA = 'metrics_schema'
MIN_FUSION_READS = 'min_fusion_reads'
MUTATION_NONSYN = 'mutation_nonsyn'
NORMAL_ID = 'normalid'
ONCO_LIST = 'oncolist'
OUT_DIR = 'out_dir'
PATIENT = 'patient'
PATIENT_ID = 'patientid'
PCT_V7_ABOVE_80X = 'pct_v7_above_80x'
PROVENANCE = 'provenance'
R_SCRIPT_DIR = 'r_script_dir'
REQUIRE_COMPLETE = 'require_complete'
SAMPLE_ANATOMICAL_SITE = 'sample_anatomical_site'
SAMPLE_PRIMARY_OR_METASTASIS = 'sample_primary_or_metastasis'
SAMPLE_TYPE = 'sample_type'
EXTRACTION_DIR = 'extraction_dir'
SEG_FILE = 'segfile'
SEQUENZA_FILE = 'sequenza_file'
SEX = 'sex'
STUDY_ID = 'studyid'
TGCA_CODE = 'tcgacode'
TGCA_DATA = 'tcgadata'
TMBCOMP = 'tmbcomp'
TUMOUR_ID = 'tumourid'
VALIDATE = 'validate'
WHIZBAM_URL = 'whizbam_url'

# lists of fields by section
SAMPLE_META_FIELDS = [
    SAMPLE_TYPE,
    CANCER_TYPE,
    CANCER_TYPE_DESCRIPTION,
    DATE_SAMPLE_RECEIVED,
    MEAN_COVERAGE,
    PCT_V7_ABOVE_80X,
    SAMPLE_ANATOMICAL_SITE,
    SAMPLE_PRIMARY_OR_METASTASIS,
    SEX
]
