#! /usr/bin/env bash

# 'source' this file to run tests
# assumes djerba and djerba_test_data are in ~/git
# update module and filename as necessary for additional dev releases

module load djerba/1.0.0-dev13
export PYTHONPATH=${HOME}/git/djerba/src/lib:$PYTHONPATH
export PATH=${HOME}/git/djerba/src/bin:$PATH
export DJERBA_BASE_DIR=${HOME}/git/djerba/src/lib/djerba
export DJERBA_TEST_DATA=${HOME}/git/djerba_test_data
export DJERBA_GSICAPBENCH_DATA=/.mounts/labs/CGI/gsi/djerba_test/GSICAPBENCH_djerba_latest
export DJERBA_BASE_DIR=$HOME/git/djerba/src/lib/djerba
export DJERBA_DATA_DIR=$HOME/git/djerba/src/lib/djerba/data
export DJERBA_PRIVATE_DIR=$HOME/workspace/djerba/env/private
