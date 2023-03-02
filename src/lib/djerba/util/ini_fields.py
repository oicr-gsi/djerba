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
MSI_FILE = 'msi_file'
MUTATION_NONSYN = 'mutation_nonsyn'
NORMAL_ID = 'normalid'
ONCO_LIST = 'oncolist'
ONCOKB_CACHE = 'oncokb_cache'
ONCOTREE_DATA = 'oncotree_data'
ONCOTREE_CODE = 'oncotree_code' # was CANCER_TYPE_DETAILED
PATIENT = 'patient'
PATIENT_ID = 'patientid'
PCT_V7_ABOVE_80X = 'pct_v7_above_80x'
PIPELINE_VERSION = 'pipeline_version'
PLOIDY = 'ploidy'
PROJECT_ID = 'projectid'
PROVENANCE = 'provenance'
PURITY = 'purity'
REPORT_VERSION = 'report_version'
REQ_ID = 'requisition_id'
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
        MSI_FILE,
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
        SEX,
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
        MSI_FILE,
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
        MEAN_COVERAGE,
        ONCOTREE_CODE,
        PATIENT,
        PROJECT_ID,
        PCT_V7_ABOVE_80X,
        REPORT_VERSION,
        REQ_ID,
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
        SEX,
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
