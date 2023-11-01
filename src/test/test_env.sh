#! /usr/bin/env bash

# 'source' this file to run tests
# assumes djerba and djerba_test_data are in ~/git
# update module and filename as necessary for additional dev releases

if [ -z "${DJERBA_SOURCE_DIR}" ]; then
	echo "Must set environment variable DJERBA_SOURCE_DIR"
else
	module load djerba
	export PYTHONPATH=${DJERBA_SOURCE_DIR}/src/lib:$PYTHONPATH
	export PATH=${DJERBA_SOURCE_DIR}/src/bin:$PATH
	export DJERBA_BASE_DIR=${DJERBA_SOURCE_DIR}/src/lib/djerba
	export DJERBA_DATA_DIR=${DJERBA_SOURCE_DIR}/src/lib/djerba/data
	export DJERBA_PRIVATE_DIR=${HOME}/workspace/djerba/env/private
	export DJERBA_TEST_DATA=${HOME}/git/djerba_test_data
	export DJERBA_GSICAPBENCH_DATA=/.mounts/labs/CGI/gsi/djerba_test/GSICAPBENCH_djerba_latest
fi