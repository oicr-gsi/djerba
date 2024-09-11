"""
TAR-specific constants.
"""

# Configure parameters
DONOR = 'donor'
ONCOTREE = 'oncotree_code'
ASSAY = 'assay'
CBIO_ID = 'cbio_id'
TUMOUR_ID = 'tumour_id'
NORMAL_ID = 'normal_id'
MAF_FILE = 'maf_file' 
MAF_NORMAL_FILE = 'maf_file_normal'
WF_MAF = 'maf_tumour' 
WF_MAF_NORMAL = 'maf_normal'

FREQUENCY_FILE = "plugins/tar/snv_indel/data/TGL.frequency.20210609.annot.txt"
GENES_TO_KEEP = ["BRCA2", 
                 "BRCA1",
                 "PALB2",
                 "TP53",
                 "APC",
                 "EPCAM",
                 "PMS2",
                 "MLH1",
                 "MSH2",
                 "MSH6",
                 "CCNE1",
                 "NF1",
                 "CDH1",
                 "VHL"]
CLEAN_COLUMNS = ["t_depth", 
                 "t_ref_count", 
                 "t_alt_count", 
                 "n_depth", 
                 "n_ref_count", 
                 "n_alt_count",
                 "gnomAD_AF"]
