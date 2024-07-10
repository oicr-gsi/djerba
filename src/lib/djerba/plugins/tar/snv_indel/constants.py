"""
TAR-specific constants.
"""

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
                 "ABCB1",
                 "CCNE1"]
CLEAN_COLUMNS = ["t_depth", 
                 "t_ref_count", 
                 "t_alt_count", 
                 "n_depth", 
                 "n_ref_count", 
                 "n_alt_count",
                 "gnomAD_AF"]
