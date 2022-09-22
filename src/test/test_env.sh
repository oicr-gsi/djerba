#! /usr/bin/env bash

# This script sets up the environment to run tests from source files in $DJERBA_SOURCE_DIR.
# Tests make use of the private djerba_test_data_lfs repo and GSICAPBENCH data.

# Example usage:
# export DJERBA_SOURCE_DIR=$HOME/git/djerba
# source $HOME/git/djerba/test/test_env.sh

if [ -z "${DJERBA_SOURCE_DIR}" ]; then
    echo "Must set environment variable DJERBA_SOURCE_DIR"
else
    module load djerba
    export PYTHONPATH=${DJERBA_SOURCE_DIR}/src/lib:$PYTHONPATH
    export PATH=${DJERBA_SOURCE_DIR}/src/bin:$PATH
    export DJERBA_TEST_DATA=/.mounts/labs/CGI/gsi/djerba_test/djerba_test_data_lfs
    export DJERBA_GSICAPBENCH_DATA=/.mounts/labs/CGI/gsi/djerba_test/GSICAPBENCH_djerba_latest
fi
