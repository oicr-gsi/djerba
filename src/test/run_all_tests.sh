#! /usr/bin/env bash

set -euo pipefail

echo "Running core tests..."
./src/test/core/test_core.py -v
echo "Running mini-Djerba tests..."
./src/test/util/mini/test_mini.py -v
echo "Running plugin discovery tests, may take ~5 minutes..."
python3 -m unittest discover -s src/lib/djerba  -p "*_test.py" -v
echo "Running benchmarking and other utility tests, may take ~10 minutes..."
./src/test/util/test_util.py -v
