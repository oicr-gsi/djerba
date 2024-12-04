"""Field names for the input INI file"""

# section names
INPUTS = 'inputs'
SETTINGS = 'settings'
DISCOVERED = 'discovered'
VERSIONS = 'versions'

# parameter names
ASSAY_VERSION = 'assay_version'
ARCHIVE_NAME = 'archive_name'
ARCHIVE_URL = 'archive_url'
BED_PATH = 'bed_path'
CBIO_STUDY_ID = 'cbio_study_id'
CBIO_PROJECT_PATH = 'cbio_studies_path'
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
MRDETECT_FILE = 'mrdetect_file'
MSI_FILE = 'msi_file'
MUTATION_NONSYN = 'mutation_nonsyn'
NORMAL_ID = 'normalid'
ONCO_LIST = 'oncolist'
ONCOKB_CACHE = 'oncokb_cache'
ONCOTREE_DATA = 'oncotree_data'
ONCOTREE_CODE = 'oncotree_code' # was CANCER_TYPE_DETAILED
PATIENT = 'patient'
PATIENT_ID = 'patientid'
PATIENT_ID_RAW = 'patientid_raw'
PCT_V7_ABOVE_80X = 'pct_v7_above_80x'
PINERY_URL = 'pinery_url'
PIPELINE_VERSION = 'pipeline_version'
PLOIDY = 'ploidy'
PROJECT_ID = 'projectid'
PROVENANCE = 'provenance'
PURITY = 'purity'
QCETL_CACHE = 'qcetl_cache'
REPORT_VERSION = 'report_version'
REQ_ID = 'requisition_id'
REQ_APPROVED_DATE = 'req_approved_date'
SAMPLE_ANATOMICAL_SITE = 'sample_anatomical_site'
SAMPLE_NAME_WG_N = 'sample_name_normal' # wgs or tar normal
SAMPLE_NAME_WG_T = 'sample_name_tumour' # wgs or tar tumour
SAMPLE_NAME_WT_T = 'sample_name_aux' # transcriptome or shallow
SAMPLE_TYPE = 'sample_type'
SEQUENZA_FILE = 'sequenza_file'
SEQUENZA_GAMMA = 'sequenza_gamma'
SEQUENZA_REVIEWER_1 = 'sequenza_reviewer_1'
SEQUENZA_REVIEWER_2 = 'sequenza_reviewer_2'
SEQUENZA_SOLUTION = 'sequenza_solution'
STUDY_ID = 'studyid'
TARGET_COVERAGE = 'target_coverage'
TCGA_CODE = 'tcgacode'
TCGA_DATA = 'tcgadata'
TECHNICAL_NOTES = 'technical_notes'
TMBCOMP = 'tmbcomp'
TUMOUR_ID = 'tumourid'
WHIZBAM_URL = 'whizbam_url'

# Parameters for versions of software and other
PICARD_VERSION = 'picard_version'
PICARD_LINK = 'picard_link'
REFERENCE_GENOME_VERSION = 'reference_genome_version'
REFERENCE_GENOME_LINK = 'reference_genome_link'
BWAMEM_VERSION = 'bwamem_version'
BWAMEM_LINK = 'bwamem_link'
GATK_VERSION = 'GATK_version'
GATK_LINK = 'GATK_link'
MUTECT2_VERSION = 'MuTect2_version'
MUTECT2_LINK = 'MuTect2_link'
VARIANTEFFECTPREDICTOR_VERSION = 'VariantEffectPredictor_version'
VARIANTEFFECTPREDICTOR_LINK = 'VariantEffectPredictor_link'
MANE_VERSION = 'MANE_version'
MANE_LINK = 'MANE_link'
SEQUENZA_VERSION = 'Sequenza_version'
SEQUENZA_LINK = 'Sequenza_link'
MICROSATELLITE_VERSION = 'Microsatellite_version'
MICROSATELLITE_LINK = 'Microsatellite_link'
STAR_VERSION = 'STAR_version'
STAR_LINK = 'STAR_link'
RSEM_VERSION = 'RSEM_version' 
RSEM_LINK = 'RSEM_link'
STARFUSION_VERSION = 'STARFusion_version'
STARFUSION_LINK = 'STARFusion_link'
ARRIBA_VERSION = 'Arriba_version'
ARRIBA_LINK = 'Arriba_link'
MAVIS_VERSION = 'MAVIS_version'
MAVIS_LINK = 'MAVIS_link'

# schemas to represent required structure for the INI file
# core schema for plugins
# TODO move Sequenza reviewers from core schema into WGTS/WGS plugin settings?

# work in progress on INI constants for plugin structure
CORE = 'core'
SCHEMA_CORE = {
    CORE: [
        MEAN_COVERAGE,
        ONCOTREE_CODE,
        PATIENT,
        PCT_V7_ABOVE_80X,
        PROJECT_ID,
        REPORT_VERSION,
        REQ_ID,
        REQ_APPROVED_DATE,
        SAMPLE_ANATOMICAL_SITE,
        SAMPLE_TYPE,
        SEQUENZA_REVIEWER_1,
        SEQUENZA_REVIEWER_2,
        STUDY_ID,
        TCGA_CODE
    ],
    SETTINGS: [
        ASSAY_VERSION,
        ARCHIVE_NAME,
        ARCHIVE_URL,
        BED_PATH,
        GEP_REFERENCE,
        MIN_FUSION_READS,
        ONCOKB_CACHE,
        PIPELINE_VERSION,
        PROVENANCE,
        TCGA_DATA,
        WHIZBAM_URL
    ]
}

# old-style schemas


SCHEMA_DEFAULT = {
    DISCOVERED: [
        CBIO_STUDY_ID,
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
        MEAN_COVERAGE,
        MSI_FILE,
        MRDETECT_FILE,
        MUTATION_NONSYN,
        NORMAL_ID,
        ONCO_LIST,
        ONCOTREE_DATA,
        PATIENT_ID,
        PCT_V7_ABOVE_80X,
        PLOIDY,
        PURITY,
        SAMPLE_NAME_WG_N,
        SAMPLE_NAME_WG_T,
        SAMPLE_NAME_WT_T,
        SEQUENZA_GAMMA,
        SEQUENZA_FILE,
        SEQUENZA_SOLUTION,
        TARGET_COVERAGE,
        TECHNICAL_NOTES,
        TMBCOMP,
        TUMOUR_ID
    ],
    INPUTS: [
        ONCOTREE_CODE,
        PATIENT,
        PROJECT_ID,
        REPORT_VERSION,
        REQ_ID,
        REQ_APPROVED_DATE,
        SAMPLE_ANATOMICAL_SITE,
        SAMPLE_TYPE,
        SEQUENZA_REVIEWER_1,
        SEQUENZA_REVIEWER_2,
        STUDY_ID,
        TCGA_CODE
    ],
    SETTINGS: [
        ASSAY_VERSION,
        ARCHIVE_NAME,
        ARCHIVE_URL,
        BED_PATH,
        CBIO_PROJECT_PATH,
        GEP_REFERENCE,
        MIN_FUSION_READS,
        ONCOKB_CACHE,
        PINERY_URL,
        PIPELINE_VERSION,
        PROVENANCE,
        QCETL_CACHE,
        TCGA_DATA,
        WHIZBAM_URL
    ],
    VERSIONS: [
        PICARD_VERSION,
        PICARD_LINK,
        REFERENCE_GENOME_VERSION,
        REFERENCE_GENOME_LINK,
        BWAMEM_VERSION,
        BWAMEM_LINK, 
        GATK_VERSION,
        GATK_LINK,
        MUTECT2_VERSION,
        MUTECT2_LINK,
        VARIANTEFFECTPREDICTOR_VERSION,
        VARIANTEFFECTPREDICTOR_LINK,
        MANE_VERSION,
        MANE_LINK,
        SEQUENZA_VERSION,
        SEQUENZA_LINK,
        MICROSATELLITE_VERSION,
        MICROSATELLITE_LINK,
        STAR_VERSION,
        STAR_LINK,
        RSEM_VERSION, 
        RSEM_LINK,
        STARFUSION_VERSION,
        STARFUSION_LINK,
        ARRIBA_VERSION,
        ARRIBA_LINK,
        MAVIS_VERSION,
        MAVIS_LINK
   ]
}

SCHEMA_WGS_ONLY = {
    DISCOVERED: [
        CBIO_STUDY_ID,
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
        MEAN_COVERAGE,
        MRDETECT_FILE,
        MSI_FILE,
        MUTATION_NONSYN,
        NORMAL_ID,
        ONCO_LIST,
        ONCOTREE_DATA,
        PATIENT_ID,
        PCT_V7_ABOVE_80X,
        PLOIDY,
        PURITY,
        SAMPLE_NAME_WG_N,
        SAMPLE_NAME_WG_T,
        SEQUENZA_GAMMA,
        SEQUENZA_FILE,
        SEQUENZA_SOLUTION,
        TARGET_COVERAGE,
        TECHNICAL_NOTES,
        TMBCOMP,
        TUMOUR_ID
    ],
    INPUTS: [
        ONCOTREE_CODE,
        PATIENT,
        PROJECT_ID,
        REPORT_VERSION,
        REQ_ID,
        REQ_APPROVED_DATE,
        SAMPLE_ANATOMICAL_SITE,
        SAMPLE_TYPE,
        SEQUENZA_REVIEWER_1,
        SEQUENZA_REVIEWER_2,
        STUDY_ID,
        TCGA_CODE
    ],
    SETTINGS: [
        ASSAY_VERSION,
        ARCHIVE_NAME,
        ARCHIVE_URL,
        BED_PATH,
        CBIO_PROJECT_PATH,
        GEP_REFERENCE,
        MIN_FUSION_READS,
        ONCOKB_CACHE,
        PINERY_URL,
        PIPELINE_VERSION,
        PROVENANCE,
        QCETL_CACHE,
        TCGA_DATA,
        WHIZBAM_URL
    ],
    VERSIONS: [
        PICARD_VERSION,
        PICARD_LINK,
        REFERENCE_GENOME_VERSION,
        REFERENCE_GENOME_LINK,
        BWAMEM_VERSION,
        BWAMEM_LINK, 
        GATK_VERSION,
        GATK_LINK,
        MUTECT2_VERSION,
        MUTECT2_LINK,
        VARIANTEFFECTPREDICTOR_VERSION,
        VARIANTEFFECTPREDICTOR_LINK,
        MANE_VERSION,
        MANE_LINK,
        SEQUENZA_VERSION,
        SEQUENZA_LINK,
        MICROSATELLITE_VERSION,
        MICROSATELLITE_LINK,
        STAR_VERSION,
        STAR_LINK,
        RSEM_VERSION, 
        RSEM_LINK,
        STARFUSION_VERSION,
        STARFUSION_LINK,
        ARRIBA_VERSION,
        ARRIBA_LINK,
        MAVIS_VERSION,
        MAVIS_LINK
   ]
}

SCHEMA_FAILED = {
    DISCOVERED: [
        CBIO_STUDY_ID,
        DATA_DIR,
        ENSCON,
        ENTCON,
        GENE_BED,
        GENE_LIST,
        GENOMIC_SUMMARY,
        MEAN_COVERAGE,
        MUTATION_NONSYN,
        NORMAL_ID,
        ONCO_LIST,
        ONCOTREE_DATA,
        PATIENT_ID,
        PCT_V7_ABOVE_80X,
        PLOIDY,
        PURITY,
        TARGET_COVERAGE,
        TECHNICAL_NOTES,
        TMBCOMP,
        TUMOUR_ID
    ],
    INPUTS: [
        ONCOTREE_CODE,
        PATIENT,
        PROJECT_ID,
        REPORT_VERSION,
        REQ_ID,
        REQ_APPROVED_DATE,
        SAMPLE_ANATOMICAL_SITE,
        SAMPLE_TYPE,
        SEQUENZA_REVIEWER_1,
        SEQUENZA_REVIEWER_2,
        STUDY_ID,
        TCGA_CODE
    ],
    SETTINGS: [
        ASSAY_VERSION,
        ARCHIVE_NAME,
        ARCHIVE_URL,
        BED_PATH,
        CBIO_PROJECT_PATH,
        GEP_REFERENCE,
        MIN_FUSION_READS,
        ONCOKB_CACHE,
        PINERY_URL,
        PIPELINE_VERSION,
        PROVENANCE,
        QCETL_CACHE,
        TCGA_DATA,
        WHIZBAM_URL
    ],
    VERSIONS: [
        PICARD_VERSION,
        PICARD_LINK,
        REFERENCE_GENOME_VERSION,
        REFERENCE_GENOME_LINK,
        BWAMEM_VERSION,
        BWAMEM_LINK, 
        GATK_VERSION,
        GATK_LINK,
        MUTECT2_VERSION,
        MUTECT2_LINK,
        VARIANTEFFECTPREDICTOR_VERSION,
        VARIANTEFFECTPREDICTOR_LINK,
        MANE_VERSION,
        MANE_LINK,
        SEQUENZA_VERSION,
        SEQUENZA_LINK,
        MICROSATELLITE_VERSION,
        MICROSATELLITE_LINK,
        STAR_VERSION,
        STAR_LINK,
        RSEM_VERSION, 
        RSEM_LINK,
        STARFUSION_VERSION,
        STARFUSION_LINK,
        ARRIBA_VERSION,
        ARRIBA_LINK,
        MAVIS_VERSION,
        MAVIS_LINK
   ]
}
