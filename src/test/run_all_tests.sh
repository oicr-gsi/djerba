#! /usr/bin/env bash

set -euo pipefail

if [ -z "${DJERBA_BASE_DIR}" ]; then
    echo "DJERBA_BASE_DIR not set; need to do 'module load djerba'?"
    exit 1
fi

echo "Running core tests..."
./src/test/core/test_core.py -v
echo "Running mini-Djerba tests..."
./src/test/util/mini/test_mini.py -v
echo "Running plugin discovery tests, may take ~10 minutes..."
python3 -m unittest discover -s src/lib/djerba  -p "*_test.py" -v
echo "Running benchmarking and other utility tests, may take ~6 minutes..."
./src/test/util/test_util.py -v
echo "Running R scripts"
./src/lib/djerba/plugins/wgts/cnv_purple/tests/testthat/test_CNA_supporting_functions.R
