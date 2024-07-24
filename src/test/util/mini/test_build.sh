#! /usr/bin/env bash
set -euo pipefail
./mini_djerba -v setup -j $DJERBA_TEST_DATA/mini/BTCWGTS-736-v1_report.json
mkdir -p mini_djerba_test
./mini_djerba report -j $DJERBA_TEST_DATA/mini/BTCWGTS-736-v1_report.json \
	      -i $DJERBA_TEST_DATA/mini/mini_djerba.ini \
	      -s $DJERBA_TEST_DATA/mini/summary.txt \
	      -o mini_djerba_test
