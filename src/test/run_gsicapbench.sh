#! /usr/bin/env bash

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Usage: run_gsicapbench.sh \$PATH_TO_VIDARR_WORKFLOW_INPUTS \$PATH_TO_OUTPUT_DIRECTORY"
    exit 1
fi

benchmark.py --verbose report -i $1 -o $2 --apply-cache
TOTAL=6
MISSING=0
FAILED=0
for FOO in 19 32 33 73 75 88; do
    RUN=GSICAPBENCH_12$FOO
    REPORT_DIR=$PWD/$RUN
    if [ -d $REPORT_DIR ]; then
	    benchmark.py \
        --debug \
        compare \
        --report-dir /.mounts/labs/CGI/benchmark/reference/latest/$RUN \
        --report-dir $REPORT_DIR \
	|| let "FAILED += 1"
    else
        let "MISSING += 1"
    fi
done
echo "Finished comparison, with $MISSING missing runs"
let "AVAIL=$TOTAL-$MISSING"
if (($FAILED > 0)); then
    echo "ERROR: Djerba reports are NOT equivalent for $FAILED of $AVAIL available GSICAPBENCH runs"
    STATUS=5
else
    echo "Equivalent Djerba reports generated for $AVAIL of $TOTAL GSICAPBENCH runs"
fi
