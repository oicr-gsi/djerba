#!/bin/bash

# Generate a geneticist QC report for upload to the requisition system
# See Data Analysis and Reporting SOP for further details
# module prerequisites: production-tools-python, wkhtmltopdf

set -euo pipefail

# Parse command-line arguments; exit if wrong number of arguments given
if [[ $# != 1 ]]; then
    echo "Usage: $0 \$REQUISITION" 1>&2
    echo "REQUISITION = ID in req system, eg. PASS01JHU-137"
    exit 1
fi
REQUISITION=$1

# Constants
PYTHON_TOOLS_VER=17
DB_CONFIG=/.mounts/labs/gsi/secrets/cap_reports_prod_db_config_ro.ini
MISO_URL=https://miso.oicr.on.ca
DASHI_URL=https://dashi.oicr.on.ca
PINERY_URL=http://pinery.gsi.oicr.on.ca
SAMPURU_ETL=/scratch2/groups/gsi/production/sampuru-etl
QCETL_CACHE=/scratch2/groups/gsi/production/qcetl_v1

# We unload the current Python module (if any) and load production-tools-python
# Resolves version conflict, eg. 3.9 for Djerba and 3.6 for production-tools-python

# NB: Could build production-tools-python in setup.py by adding this to install_requires in setup.py:
# 'ProductionTools @ git+ssh://bitbucket.oicr.on.ca/gsi/production-tools-python@v1.5.3'
# But this was rejected as production-tools-python is large and time-consuming to build

module unload djerba djerba-dbtools pypdf2 oncokb-annotator python # this always has returncode 0
module load production-tools-python/${PYTHON_TOOLS_VER}

cap-geneticist-review-report -c ${DB_CONFIG} -m ${MISO_URL} -d ${DASHI_URL} \
  -e ${QCETL_CACHE} -s ${SAMPURU_ETL} -p ${PINERY_URL} -r ${REQUISITION} \
  -o ${REQUISITION}_qc.html

# convert to PDF
wkhtmltopdf ${REQUISITION}_qc.html ${REQUISITION}_qc.pdf
