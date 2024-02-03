#! /usr/bin/env bash

set -euo pipefail

echo "Running core tests..."
./src/test/core/test_core.py -v
echo "Running mini-Djerba tests..."
./src/test/util/mini/test_mini.py -v
