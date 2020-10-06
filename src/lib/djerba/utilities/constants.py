"""Module to define constants"""

CNA_TYPE = 'COPY_NUMBER_ALTERATION'
EXPRESSION_TYPE = 'MRNA_EXPRESSION'
MUTATION_TYPE = 'MUTATION_EXTENDED'
DEMONSTRATION_TYPE = 'DEMONSTRATION'
DISCRETE_DATATYPE = 'DISCRETE'

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
PATIENT_DATATYPE = 'PATIENT_ATTRIBUTES'
SAMPLE_DATATYPE = 'SAMPLE_ATTRIBUTES'

# keys for Elba report generation
SAMPLE_ID_KEY = 'SAMPLE_ID'
GENE_KEY = 'Gene'
CLINICAL_DATA_KEY = 'ClinData' # obsolete? depends on report JSON
GENOMIC_LANDSCAPE_KEY = 'genomicLandscape'
GENE_METRICS_KEY = 'gene_metrics'
SAMPLE_INFO_KEY = 'sample_info'
SMALL_MUTATION_INDEL_KEY = 'smallMutAndIndel' # obsolete? depends on report JSON

# keys for Djerba config
GENETIC_ALTERATIONS_KEY = 'genetic_alterations'
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
