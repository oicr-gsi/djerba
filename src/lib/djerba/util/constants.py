"""Constants for use across multiple Djerba classes"""

DATA_DIR_NAME = 'data'
SEQUENZA_PRIMARY_SOLUTION = '_primary_' # underscores are to make tab-delimited output line up better
SEQUENZA_GAMMA = 'sequenza_gamma'
SEQUENZA_PURITY_KEY = 'sequenza_purity_fraction'
SEQUENZA_PLOIDY_KEY = 'sequenza_ploidy'
TEXT_ENCODING = 'utf-8'
TMB_PER_MB_KEY = 'TMB_PER_MB'

# file names
CLINICAL_DATA_FILENAME = 'data_clinical.txt'
DATA_CNA_ONCOKB_GENES = 'data_CNA_oncoKBgenes.txt'
DATA_FUSIONS_ONCOKB = 'data_fusions_oncokb.txt'
GENOMIC_SUMMARY_FILENAME = 'genomic_summary.txt'
SEQUENZA_META_FILENAME = 'sequenza_meta.txt'
REPORT_JSON_FILENAME = 'djerba_report.json'
TECHNICAL_NOTES_FILENAME = 'technical_notes.txt'

# Gene attributes to parse R script results
COPY_STATE = 'Copy_State'
GENE = 'Gene'
PROTEIN_CHANGE = 'Protein_Change'
VARIANT_CLASSIFICATION = 'Variant_Classification'

# clinical data file headers
PATIENT_LIMS_ID = 'PATIENT_LIMS_ID'
PATIENT_STUDY_ID = 'PATIENT_STUDY_ID'
TUMOUR_SAMPLE_ID = 'TUMOUR_SAMPLE_ID'
BLOOD_SAMPLE_ID = 'BLOOD_SAMPLE_ID'
REPORT_VERSION = 'REPORT_VERSION'
SAMPLE_TYPE = 'SAMPLE_TYPE'
CANCER_TYPE = 'CANCER_TYPE'
CANCER_TYPE_DETAILED = 'CANCER_TYPE_DETAILED'
CANCER_TYPE_DESCRIPTION = 'CANCER_TYPE_DESCRIPTION'
CLOSEST_TCGA = 'CLOSEST_TCGA'
SAMPLE_ANATOMICAL_SITE = 'SAMPLE_ANATOMICAL_SITE'
MEAN_COVERAGE = 'MEAN_COVERAGE'
PCT_V7_ABOVE_80X = 'PCT_V7_ABOVE_80X'
REQ_APPROVED_DATE = 'REQ_APPROVED_DATE'
SEQUENZA_PURITY_FRACTION = 'SEQUENZA_PURITY_FRACTION'
SEQUENZA_PLOIDY = 'SEQUENZA_PLOIDY'
SEX = 'SEX'

# mode names for djerba.py
SETUP = 'setup'
CONFIGURE = 'configure'
DRAFT = 'draft'
EXTRACT = 'extract'
HTML = 'html'
PDF = 'pdf'
ALL = 'all'

# mode names for benchmark.py
# REPORT = 'report' # duplicate of top-level JSON section name; this is fine
COMPARE = 'compare'

# for running Mavis
MAVIS_SUBDIR_NAME = 'mavis'

# high-level elements of main JSON
REPORT = 'report'
SUPPLEMENTARY = 'supplementary'
CONFIG = 'config'
