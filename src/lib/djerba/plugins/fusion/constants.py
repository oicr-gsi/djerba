# constants for the CNV plugin

import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb_constants


MAKO_TEMPLATE_NAME = 'fusion_template.html'

# INI config keys
MAVIS_PATH = 'mavis path'
ARRIBA_PATH = 'arriba_path'
ONCOTREE_CODE = 'oncotree code'
ENTREZ_CONVERSION_PATH = 'entrez conv path'
MIN_FUSION_READS = 'minimum fusion reads'

# JSON results keys
TOTAL_VARIANTS = "Total variants"
CLINICALLY_RELEVANT_VARIANTS = "Clinically relevant variants"
BODY = 'body'
FRAME = 'frame'
GENE = 'gene'
GENE_URL = 'gene URL'
CHROMOSOME = 'chromosome'
FUSION = 'fusion'
MUTATION_EFFECT = 'mutation effect'
ONCOKB_LINK = 'oncokb_link'
TRANSLOCATION = 'translocation'

# other constants
ENTRCON_NAME = 'entrez_conversion.txt'

# read files from an input directory and gather information on fusions

DATA_FUSIONS_OLD = 'data_fusions.txt'
DATA_FUSIONS_ANNOTATED = 'data_fusions_oncokb_annotated.txt'
DATA_FUSIONS_NCCN_ANNOTATED = 'data_fusions_NCCN.txt'
FUSION_INDEX = 3
HUGO_SYMBOL = 'Hugo_Symbol'
NCCN_RELEVANT_VARIANTS = 'nccn_relevant_variants'