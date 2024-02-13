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
