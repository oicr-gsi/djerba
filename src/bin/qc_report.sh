#!/bin/bash

# Generate a geneticist QC report for upload to the requisition system
# See Data Analysis and Reporting SOP for further details
# module prerequisites: production-tools-python/8, wkhtmltopdf/0.12.6

set -euo pipefail

# Parse command-line arguments; exit if wrong number of arguments given
if [[ $# < 2 || $# > 3 ]]; then
    echo "Usage: $0 \$IDENTITY_ID \$IDENTITY_ALIAS [\$TUMOUR_DEPTH]" 1>&2
    echo "IDENTITY_ID = Sample ID in MISO, eg. 413576"
    echo "IDENTITY_ALIAS = Sample alias in MISO, eg. PANX_1289"
    echo "TUMOUR_DEPTH = target sequencing depth; defaults to 40"
    exit 1
fi
IDENTITY_ID=$1
IDENTITY_ALIAS=$2
if [ $# == 3 ]; then
    TUMOUR_DEPTH=$3
else
    TUMOUR_DEPTH=40
fi

# Constants
DB_CONFIG=/.mounts/labs/gsi/secrets/cap_reports_prod_db_config_ro.ini
MISO_URL=https://miso.oicr.on.ca
DASHI_URL=https://dashi.oicr.on.ca
QCETL_CACHE=/scratch2/groups/gsi/production/qcetl

# Generate the HTML report
cap-geneticist-review-report -c ${DB_CONFIG} -m ${MISO_URL} -d ${DASHI_URL} \
  -e ${QCETL_CACHE} -i ${IDENTITY_ID} -t ${TUMOUR_DEPTH} \
  -o geneticist_review_${IDENTITY_ALIAS}.html

# convert to PDF
wkhtmltopdf geneticist_review_${IDENTITY_ALIAS}.html geneticist_review_${IDENTITY_ALIAS}.pdf
