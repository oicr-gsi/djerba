ALT = 'Alteration'
ALTERATION = 'Alteration'
ALT_URL = 'Alteration_URL'
ALTERATION_UPPER_CASE = 'ALTERATION'
BODY = 'body'
CHROMOSOME = 'Chromosome'
CLINICALLY_RELEVANT_VARIANTS = 'clinically relevant variants'
CNA_PATH = 'cna_path'
EXPRESSION_METRIC = 'Expression Percentile'
GENE = 'Gene'
GENE_URL = 'Gene_URL'
HAS_EXPRESSION_DATA = 'has expression data'
HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
HUGO_SYMBOL_TITLE_CASE = 'Hugo_Symbol'
MUTATION_TYPE = 'Type'
NA = 'NA'
NORMAL_ID = 'normal_id'
ONCOGENIC = 'ONCOGENIC'
ONCOKB = 'OncoKB level'
ONCOTREE_CODE = 'oncotree code'
PERCENT_GENOME_ALTERED = 'percent genome altered'
STUDY_ID = 'study_id' 
TOTAL_VARIANTS = 'total variants'
TUMOUR_ID = 'tumour_id'
VAF_PERCENT = 'VAP (%)'

# links and locations
CENTROMERES = "data/hg38_centromeres.txt"
CNA_ANNOTATED = "data_CNA_oncoKBgenes_nonDiploid_annotated.txt"
CYTOBAND = "/data/cytoBand.txt"
GENEBED =  "data/gencode_v33_hg38_genes.bed"
ONCOLIST =  "data/20200818-oncoKBcancerGeneList.tsv"
ONCOKB_URL_BASE = 'https://www.oncokb.org/gene'
TEMPLATE_NAME = 'cnv_template.html'
WHIZBAM_BASE_URL = 'https://whizbam.oicr.on.ca'

GENOME_SIZE = 3*10**9 # TODO use more accurate value when we release a new report format

UNCLASSIFIED_CYTOBANDS = [
    "", # some genes have an empty string for cytoband
    "mitochondria",
    "not on reference assembly",
    "reserved",
    "unplaced",
    "13cen",
    "13cen, GRCh38 novel patch",
    "2cen-q11",
    "2cen-q13",
    "c10_B",
    "HSCHR6_MHC_COXp21.32",
    "HSCHR6_MHC_COXp21.33",
    "HSCHR6_MHC_COXp22.1",
    "Unknown"
]
