# collection of constants for OncoKB processing

### Djerba filenames ###

ANNOTATED_MAF = 'annotated_maf.tsv'
CACHE_CNA = 'cna_cache.json'
CACHE_FUSION = 'fusion_cache.json'
CACHE_MAF = 'maf_cache.json'
DATA_CNA_ONCOKB_GENES_NON_DIPLOID = 'data_CNA_oncoKBgenes_nonDiploid.txt'
DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED = 'data_CNA_oncoKBgenes_nonDiploid_annotated.txt'
DATA_FUSIONS_ONCOKB = 'data_fusions_oncokb.txt'
DATA_FUSIONS_ONCOKB_ANNOTATED = 'data_fusions_oncokb_annotated.txt'
ONCOKB_CLINICAL_INFO = 'oncokb_clinical_info.txt'

### OncoKB levels ###

LEVEL_1 = 'LEVEL_1'
LEVEL_2 = 'LEVEL_2'
LEVEL_3A = 'LEVEL_3A'
LEVEL_3B = 'LEVEL_3B'
LEVEL_4 = 'LEVEL_4'
LEVEL_R1 = 'LEVEL_R1'
LEVEL_R2 = 'LEVEL_R2'
ONCOGENIC = 'Oncogenic'
LIKELY_ONCOGENIC = 'Likely Oncogenic'
INCONCLUSIVE = 'Inconclusive'
UNKNOWN = 'Unknown'

FDA_APPROVED_LEVELS = [LEVEL_1, LEVEL_2, LEVEL_R1]
INVESTIGATIONAL_LEVELS = [LEVEL_3A, LEVEL_3B, LEVEL_4, LEVEL_R2]
THERAPY_LEVELS = [
    LEVEL_1,
    LEVEL_2,
    LEVEL_3A,
    LEVEL_3B,
    LEVEL_4,
    LEVEL_R1,
    LEVEL_R2,
]
ORDERED_LEVELS = [
    LEVEL_1,
    LEVEL_2,
    LEVEL_3A,
    LEVEL_3B,
    LEVEL_4,
    LEVEL_R1,
    LEVEL_R2,
    ONCOGENIC,
    LIKELY_ONCOGENIC,
    INCONCLUSIVE,
    UNKNOWN
]

### INI config keys ###

ONCOTREE_CODE = 'oncotree_code'
ONCOKB_CACHE = 'oncokb cache'
APPLY_CACHE = 'apply cache'
UPDATE_CACHE = 'update cache'


### miscellaneous ###

ALL_CURATED_GENES = '20240315-allCuratedGenes.tsv'
ONCOGENIC_UC = 'ONCOGENIC'
DEFAULT_CACHE_PATH = '/.mounts/labs/CGI/gsi/tools/djerba/oncokb_cache/scratch'
