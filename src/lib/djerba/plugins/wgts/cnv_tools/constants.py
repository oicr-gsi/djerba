"""
This file contains a list of constants to be used in the sWGS plugin.
AUTHOR: Aqsa Alam
"""

# For file provenance
MT_SEG = 'application/seg-txt$'

# For rendering
TOTAL_VARIANTS = 'Total variants'
CLINICALLY_RELEVANT_VARIANTS = 'Clinically relevant variants'
HAS_EXPRESSION_DATA = 'Has expression data'
BODY = 'Body'
GENE = 'Gene'
GENE_URL = 'Gene_URL'
CHROMOSOME = 'Chromosome'
ALTERATION = 'Alteration'
ONCOKB = 'OncoKB'
EXPRESSION_METRIC = 'Expression Percentile'
CNV_PLOT = 'cnv_plot'
TEXT_ENCODING = 'utf-8'

# Files to delete
CNV_PLOT_DATA = "cnv_plot_data.txt"
DATA_CNA = "data_CNA.txt"
DATA_CNA_ONCOKB = "data_CNA_oncoKBgenes.txt"
DATA_CNA_ONCOKB_NONDIPLOID = "data_CNA_oncoKBgenes_nonDiploid.txt"

GENEBED =  "data/gencode_v33_hg38_genes.bed"
CENTROMERES = "data/hg38_centromeres.txt"
DATA_SEGMENTS = 'data.seg'
MINIMUM_MAGNITUDE_SEG_MEAN = 0.2
GENOME_SIZE = 3*10**9 # TODO use more accurate value when we release a new report format
PERCENT_GENOME_ALTERED = 'Percent Genome Altered'
