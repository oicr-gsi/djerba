"""Field names for the input INI file"""

# section names
INPUTS = 'inputs'
SEG = 'seg'
SETTINGS = 'settings'
DISCOVERED = 'discovered'

# parameter names
AMPL = 'ampl'
BED_PATH = 'bed_path'
DATA_DIR = 'data_dir'
ENSCON = 'enscon'
ENTCON = 'entcon'
GAIN = 'gain'
GAMMA = 'gamma'
GENE_BED = 'genebed'
GENE_LIST = 'genelist'
GENOMIC_SUMMARY = 'genomic_summary'
GEP_FILE = 'gepfile'
GEP_REFERENCE = 'gep_reference'
HTZD = 'htzd'
HMZD = 'hmzd'
MAF_FILE = 'maf_file'
MAVIS_FILE = 'mavis_file'
MEAN_COVERAGE = 'mean_coverage'
MIN_FUSION_READS = 'min_fusion_reads'
MUTATION_NONSYN = 'mutation_nonsyn'
NORMAL_ID = 'normalid'
ONCO_LIST = 'oncolist'
ONCOTREE_DATA = 'oncotree_data'
ONCOTREE_CODE = 'oncotree_code' # was CANCER_TYPE_DETAILED
PATIENT = 'patient'
PATIENT_ID = 'patientid'
PCT_V7_ABOVE_80X = 'pct_v7_above_80x'
PROVENANCE = 'provenance'
REPORT_VERSION = 'report_version'
SAMPLE_ANATOMICAL_SITE = 'sample_anatomical_site'
SAMPLE_TYPE = 'sample_type'
SEQUENZA_FILE = 'sequenza_file'
SEX = 'sex'
STUDY_ID = 'studyid'
TCGA_CODE = 'tcgacode'
TCGA_DATA = 'tcgadata'
TMBCOMP = 'tmbcomp'
TUMOUR_ID = 'tumourid'
WHIZBAM_URL = 'whizbam_url'

# schema to represent required structure for the INI file
SCHEMA = {
    DISCOVERED: [
        DATA_DIR,
        ENSCON,
        ENTCON,
        GAMMA,
        GENE_BED,
        GENE_LIST,
        GENOMIC_SUMMARY,
        GEP_FILE,
        MAF_FILE,
        MAVIS_FILE,
        MUTATION_NONSYN,
        ONCO_LIST,
        ONCOTREE_DATA,
        SEQUENZA_FILE,
        TMBCOMP
    ],
    INPUTS: [
        MEAN_COVERAGE,
        NORMAL_ID,
        ONCOTREE_CODE,
        PATIENT,
        PATIENT_ID,
        PCT_V7_ABOVE_80X,
        REPORT_VERSION,
        SAMPLE_ANATOMICAL_SITE,
        SAMPLE_TYPE,
        SEX,
        STUDY_ID,
        TCGA_CODE,
        TUMOUR_ID
    ],
    SEG: [
        GAIN,
        AMPL,
        HTZD,
        HMZD
    ],
    SETTINGS: [
        BED_PATH,
        GEP_REFERENCE,
        MIN_FUSION_READS,
        PROVENANCE,
        TCGA_DATA,
        WHIZBAM_URL
    ]
}
