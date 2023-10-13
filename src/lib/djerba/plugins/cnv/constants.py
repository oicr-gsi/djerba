# constants for the CNV plugin

import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb_constants

# INI param names
# these params are also used by other plugins; TODO remove redundancy
SEQUENZA_PATH = 'sequenza_path'
SEQUENZA_GAMMA = 'sequenza_gamma'
SEQUENZA_SOLUTION = 'sequenza_solution'
PURITY = 'purity'
TUMOUR_ID = 'tumour_id'
ONCOTREE_CODE = oncokb_constants.ONCOTREE_CODE

# keys for JSON output
ALTERATION = 'Alteration'
CHROMOSOME = 'Chromosome'
EXPRESSION_PERCENTILE = 'Expression Percentile'
GENE = 'Gene'
GENE_URL = 'Gene_URL'
ONCOKB = core_constants.ONCOKB
HAS_EXPRESSION_DATA = 'has expression data'
PERCENT_GENOME_ALTERED = 'percent genome altered'
TOTAL_VARIANTS = 'total variants'
CLINICALLY_RELEVANT_VARIANTS = 'clinically relevant variants'
CNV_PLOT = 'cnv plot'
BODY = 'body'

# filenames
COPY_STATE_FILE = 'copy_states.json'
