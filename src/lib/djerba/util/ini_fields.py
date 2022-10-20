"""Field names for the input INI file"""

# section names
INPUTS = 'inputs'
SETTINGS = 'settings'
DISCOVERED = 'discovered'

# parameter names
ARCHIVE_DIR = 'archive_dir'
ASSAY_NAME = 'assay_name'
BED_PATH = 'bed_path'
DATA_DIR = 'data_dir'
ENSCON = 'enscon'
ENTCON = 'entcon'
GENE_BED = 'genebed'
GENE_LIST = 'genelist'
GENOMIC_SUMMARY = 'genomic_summary'
GEP_FILE = 'gepfile'
GEP_REFERENCE = 'gep_reference'
LOG_R_AMPL = 'ampl'
LOG_R_GAIN = 'gain'
LOG_R_HTZD = 'htzd'
LOG_R_HMZD = 'hmzd'
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
PLOIDY = 'ploidy'
PROVENANCE = 'provenance'
PURITY = 'purity'
REPORT_VERSION = 'report_version'
REQ_APPROVED_DATE = 'req_approved_date'
SAMPLE_ANATOMICAL_SITE = 'sample_anatomical_site'
SAMPLE_NAME_WG_N = 'sample_name_whole_genome_normal' # whole genome, normal
SAMPLE_NAME_WG_T = 'sample_name_whole_genome_tumour' # whole genome, tumour
SAMPLE_NAME_WT_T = 'sample_name_whole_transcriptome' # whole transcriptome, tumour
SAMPLE_TYPE = 'sample_type'
SEQUENZA_FILE = 'sequenza_file'
SEQUENZA_GAMMA = 'sequenza_gamma'
SEQUENZA_REVIEWER_1 = 'sequenza_reviewer_1'
SEQUENZA_REVIEWER_2 = 'sequenza_reviewer_2'
SEQUENZA_SOLUTION = 'sequenza_solution'
SEX = 'sex'
STUDY_ID = 'studyid'
TCGA_CODE = 'tcgacode'
TCGA_DATA = 'tcgadata'
TECHNICAL_NOTES = 'technical_notes'
TMBCOMP = 'tmbcomp'
TUMOUR_ID = 'tumourid'
WHIZBAM_URL = 'whizbam_url'

# schemas to represent required structure for the INI file
SCHEMA_DEFAULT = {
    DISCOVERED: [
        DATA_DIR,
        ENSCON,
        ENTCON,
        LOG_R_AMPL,
        LOG_R_GAIN,
        LOG_R_HMZD,
        LOG_R_HTZD,
        GENE_BED,
        GENE_LIST,
        GENOMIC_SUMMARY,
        GEP_FILE,
        MAF_FILE,
        MAVIS_FILE,
        MUTATION_NONSYN,
        NORMAL_ID,
        ONCO_LIST,
        ONCOTREE_DATA,
        PATIENT_ID,
        PLOIDY,
        PURITY,
        SAMPLE_NAME_WG_N,
        SAMPLE_NAME_WG_T,
        SAMPLE_NAME_WT_T,
        SEQUENZA_GAMMA,
        SEQUENZA_FILE,
        SEQUENZA_SOLUTION,
        TECHNICAL_NOTES,
        TMBCOMP,
        TUMOUR_ID
    ],
    INPUTS: [
        ASSAY_NAME,
        MEAN_COVERAGE,
        ONCOTREE_CODE,
        PATIENT,
        PCT_V7_ABOVE_80X,
        REPORT_VERSION,
        REQ_APPROVED_DATE,
        SAMPLE_ANATOMICAL_SITE,
        SAMPLE_TYPE,
        SEQUENZA_REVIEWER_1,
        SEQUENZA_REVIEWER_2,
        SEX,
        STUDY_ID,
        TCGA_CODE
    ],
    SETTINGS: [
        ARCHIVE_DIR,
        BED_PATH,
        GEP_REFERENCE,
        MIN_FUSION_READS,
        PROVENANCE,
        TCGA_DATA,
        WHIZBAM_URL
    ]
}

SCHEMA_WGS_ONLY = {
    DISCOVERED: [
        DATA_DIR,
        ENSCON,
        ENTCON,
        LOG_R_AMPL,
        LOG_R_GAIN,
        LOG_R_HMZD,
        LOG_R_HTZD,
        GENE_BED,
        GENE_LIST,
        GENOMIC_SUMMARY,
        MAF_FILE,
        MUTATION_NONSYN,
        NORMAL_ID,
        ONCO_LIST,
        ONCOTREE_DATA,
        PATIENT_ID,
        PLOIDY,
        PURITY,
        SAMPLE_NAME_WG_N,
        SAMPLE_NAME_WG_T,
        SEQUENZA_GAMMA,
        SEQUENZA_FILE,
        SEQUENZA_SOLUTION,
        TECHNICAL_NOTES,
        TMBCOMP,
        TUMOUR_ID
    ],
    INPUTS: [
        ASSAY_NAME,
        MEAN_COVERAGE,
        ONCOTREE_CODE,
        PATIENT,
        PCT_V7_ABOVE_80X,
        REPORT_VERSION,
        REQ_APPROVED_DATE,
        SAMPLE_ANATOMICAL_SITE,
        SAMPLE_TYPE,
        SEQUENZA_REVIEWER_1,
        SEQUENZA_REVIEWER_2,
        SEX,
        STUDY_ID,
        TCGA_CODE
    ],
    SETTINGS: [
        ARCHIVE_DIR,
        BED_PATH,
        GEP_REFERENCE,
        MIN_FUSION_READS,
        PROVENANCE,
        TCGA_DATA,
        WHIZBAM_URL
    ]
}

SCHEMA_FAILED = {
    DISCOVERED: [
        DATA_DIR,
        ENSCON,
        ENTCON,
        GENE_BED,
        GENE_LIST,
        GENOMIC_SUMMARY,
        MUTATION_NONSYN,
        NORMAL_ID,
        ONCO_LIST,
        ONCOTREE_DATA,
        PATIENT_ID,
        PLOIDY,
        PURITY,
        TECHNICAL_NOTES,
        TMBCOMP,
        TUMOUR_ID
    ],
    INPUTS: [
        ASSAY_NAME,
        MEAN_COVERAGE,
        ONCOTREE_CODE,
        PATIENT,
        PCT_V7_ABOVE_80X,
        REPORT_VERSION,
        REQ_APPROVED_DATE,
        SAMPLE_ANATOMICAL_SITE,
        SAMPLE_TYPE,
        SEQUENZA_REVIEWER_1,
        SEQUENZA_REVIEWER_2,
        SEX,
        STUDY_ID,
        TCGA_CODE
    ],
    SETTINGS: [
        ARCHIVE_DIR,
        BED_PATH,
        GEP_REFERENCE,
        MIN_FUSION_READS,
        PROVENANCE,
        TCGA_DATA,
        WHIZBAM_URL
    ]
}
