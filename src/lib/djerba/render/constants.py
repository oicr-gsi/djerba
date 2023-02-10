# top-level variable names
APPROVED_BIOMARKERS = 'approved_biomarkers'
ASSAY_TYPE = 'assay_type'
AUTHOR = 'author'
DJERBA_VERSION = 'djerba_version'
PIPELINE_VERSION = 'pipeline_version'
OICR_LOGO = 'oicr_logo'
PATIENT_INFO = 'patient_info'
SAMPLE_INFO = 'sample_info_and_quality'
GENOMIC_SUMMARY = 'genomic_summary'
GENOMIC_LANDSCAPE_INFO = 'genomic_landscape_info'
INVESTIGATIONAL_THERAPIES = 'investigational_therapies'
COVERAGE_THRESHOLDS = 'coverage_thresholds'
SMALL_MUTATIONS_AND_INDELS = 'small_mutations_and_indels'
TOP_ONCOGENIC_SOMATIC_CNVS = 'oncogenic_somatic_CNVs'
SUPPLEMENTARY_GENE_INFO = 'gene_info'
STRUCTURAL_VARIANTS_AND_FUSIONS = 'structural_variants_and_fusions'
TMB_PLOT = 'tmb_plot'
VAF_PLOT = 'vaf_plot'
CNV_PLOT = 'cnv_plot'
PGA_PLOT = 'pga_plot'
FAILED = 'failed'
PURITY_FAILURE = 'purity_failure'
ASSAY_WGTS = 'WGTS'
ASSAY_WGS = 'WGS'
REPORT_DATE = 'report_date'
TECHNICAL_NOTES = 'technical_notes'

# constants for the patient info table
ASSAY_NAME = 'Assay'
DATE_OF_REPORT = 'Date of Report'
REQ_ID = 'Requisition ID'
REQ_APPROVED_DATE = 'Requisition Approved'
REPORT_ID = 'Report ID'
PROJECT = 'Project'
STUDY = 'Study'
PATIENT_STUDY_ID = 'Patient Study ID'
PATIENT_LIMS_ID = 'Patient LIMS ID'
NAME = 'Patient Name'
DOB = 'Patient DOB'
SEX = 'Patient Genetic Sex'
PHYSICIAN = 'Physician'
LICENCE_NUMBER = 'Physician Licence #'
PHONE_NUMBER = 'Physician Phone #'
HOSPITAL = 'Physician Hospital'
REQUISITIONER_EMAIL = 'Requisitioner Email'
PRIMARY_CANCER = 'Primary cancer'
SITE_OF_BIOPSY_OR_SURGERY = 'Site of biopsy/surgery'
TUMOUR_SAMPLE_ID = 'Tumour Sample ID'
BLOOD_SAMPLE_ID = 'Blood Sample ID'
PATIENT_INFO_CONSTANT_FIELDS = {
    DOB: 'yyyy/mm/dd',
    PHYSICIAN: 'LAST, FIRST',
    NAME: 'LAST NAME, FIRST NAME',
    LICENCE_NUMBER: 'nnnnnnnn',
    PHONE_NUMBER: 'nnn-nnn-nnnn',
    HOSPITAL: 'HOSPITAL NAME AND ADDRESS',
    REQUISITIONER_EMAIL: '<a href="mailto:NAME@DOMAIN.COM" class="email">NAME@DOMAIN.COM</a>'
}

# constants for the sample info and quality table
CALLABILITY_PERCENT = 'Callability (%)'
COVERAGE_MEAN = 'Coverage (mean)'
ONCOTREE_CODE = 'OncoTree code'
PLOIDY = 'Estimated Ploidy'
PURITY_PERCENT = 'Estimated Cancer Cell Content (%)'
SAMPLE_TYPE = 'Sample Type'

# constants for the investigational therapies table
GENE = 'Gene'
GENE_URL = 'Gene_URL'
GENES_AND_URLS = 'Genes_and_URLs'
ALT = 'Alteration'
ALT_URL = 'Alteration_URL'
TREATMENT = 'Treatment'
ONCOKB = 'OncoKB'

# constants for oncogenic small mutations and indels table (also shares with investigational therapies)
BODY = 'Body'
HAS_EXPRESSION_DATA = 'Has expression data'
CLINICALLY_RELEVANT_VARIANTS = 'Clinically relevant variants'
TOTAL_VARIANTS = 'Total variants'
CHROMOSOME = 'Chr.'
DEPTH = 'Depth'
PROTEIN = 'Protein'
PROTEIN_URL = 'Protein_URL'
MUTATION_TYPE = 'Type'
EXPRESSION_METRIC = 'Expr. (%)'
VAF_PERCENT = 'VAF (%)'
VAF_NOPERCENT = 'VAF'
TUMOUR_ALT_COUNT = 't_alt_count'
TUMOUR_DEPTH = 't_depth'
COPY_STATE = 'Copy State'
LOH_STATE = 'LOH (ABratio)'

# constants for the genomic landscape table
TMB_TOTAL = 'Tumour Mutation Burden'
TMB_PER_MB = 'TMB per megabase'
PERCENT_GENOME_ALTERED = 'Percent Genome Altered'
CANCER_SPECIFIC_PERCENTILE = 'Cancer-specific Percentile'
CANCER_SPECIFIC_COHORT = 'Cancer-specific Cohort'
PAN_CANCER_PERCENTILE = 'Pan-cancer Percentile'
PAN_CANCER_COHORT = 'Pan-cancer Cohort'

# constants for the CNV table (also shares with investigational therapies)
ALTERATION = 'Alteration'

# constants for SV & fusions table (also shares with above)
FUSION = 'Fusion'
FRAME = 'Frame'
MUTATION_EFFECT = 'Mutation effect'

# constants for supplementary info table (also shares with above)
SUMMARY = 'Summary'

# coverage thresholds
NORMAL_MIN = 'Normal min'
NORMAL_TARGET = 'Normal target'
TUMOUR_MIN = 'Tumour min'
TUMOUR_TARGET = 'Tumour target'

# constants for other biomarkers
MSI = "MSI"
TMB = "TMB"
METRIC_CALL = 'Genomic biomarker call'
METRIC_VALUE = 'Genomic biomarker value'
METRIC_TEXT = 'Genomic biomarker text'
METRIC_PLOT = 'Genomic biomarker plot'
GENOMIC_BIOMARKERS = 'genomic_biomarkers'
