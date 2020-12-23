"""Module to define constants"""

# genetic_alteration datatypes
CNA_TYPE = 'COPY_NUMBER_ALTERATION'
EXPRESSION_TYPE = 'MRNA_EXPRESSION'
MUTATION_TYPE = 'MUTATION_EXTENDED'
SEGMENTED_TYPE = 'SEGMENTED'
CUSTOM_ANNOTATION_TYPE = 'CUSTOM_ANNOTATION'
DISCRETE_DATATYPE = 'DISCRETE'
SEG_DATATYPE = 'SEG'

# metadata keys for cBioPortal
DATATYPE_KEY = 'datatype'
DATA_FILENAME_KEY = 'data_filename'
GENETIC_ALTERATION_TYPE_KEY = 'genetic_alteration_type'
PROFILE_NAME_KEY = 'profile_name'
PROFILE_DESCRIPTION_KEY = 'profile_description'

SHOW_PROFILE_IN_ANALYSIS_TAB_KEY = 'show_profile_in_analysis_tab'
STABLE_ID_KEY = 'stable_id'
STUDY_ID_KEY = 'cancer_study_identifier'

CANCER_TYPE_DATATYPE = 'CANCER_TYPE'
CASE_LIST_DATATYPE = 'CASE_LIST'
CUSTOM_DATATYPE='CUSTOM' # Djerba only, not used by cBioPortal
PATIENT_DATATYPE = 'PATIENT_ATTRIBUTES'
SAMPLE_DATATYPE = 'SAMPLE_ATTRIBUTES'
MAF_DATATYPE = 'MAF'

# keys for Elba report generation
ELBA_DB_USER = 'ELBA_DB_USER'
ELBA_DB_PASSWORD = 'ELBA_DB_PASSWORD'

## keys for sample attributes
CANCER_TYPE_KEY = 'CANCER_TYPE'
CANCER_TYPE_DETAILED_KEY = 'CANCER_TYPE_DETAILED'
CANCER_TYPE_DESCRIPTION_KEY = 'CANCER_TYPE_DESCRIPTION'
COSMIC_SIGS_KEY = 'COSMIC_SIGS'
SAMPLE_ID_KEY = 'SAMPLE_ID'
SEQUENZA_PLOIDY_KEY = 'SEQUENZA_PLOIDY'
SEQUENZA_PURITY_FRACTION_KEY = 'SEQUENZA_PURITY_FRACTION'
TMB_PER_MB_KEY = 'TMB_PER_MB'
FRACTION_GENOME_ALTERED_KEY = 'FRACTION_GENOME_ALTERED'

## other
GENE_KEY = 'Gene'
CLINICAL_DATA_KEY = 'ClinData' # obsolete? depends on report JSON
GENOMIC_LANDSCAPE_KEY = 'genomicLandscape'
GENE_METRICS_KEY = 'gene_metrics'
SAMPLE_INFO_KEY = 'sample_info'
SMALL_MUTATION_INDEL_KEY = 'smallMutAndIndel' # obsolete? depends on report JSON

# keys for Djerba config
CLINICAL_REPORT_META_KEY = 'clinical_report_meta'
GENETIC_ALTERATIONS_KEY = 'genetic_alterations'
REVIEW_STATUS_KEY = 'review_status'
SAMPLE_NAME_KEY = 'sample_name'
SAMPLES_KEY = 'samples'
STUDY_META_KEY = 'study_meta'

# for constructing paths to supplementary data files
DATA_DIRNAME = 'data'

# fields for cBioPortal study metadata
REQUIRED_STUDY_META_FIELDS = [
    'type_of_cancer',
    STUDY_ID_KEY,
    'name',
    'description',
    'short_name'
]
OPTIONAL_STUDY_META_FIELDS = [
    'citation',
    'pmid',
    'groups',
    'add_global_case_list',
    'tags_file'
]

# default text encoding
TEXT_ENCODING = 'utf-8'
