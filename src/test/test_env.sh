#! /usr/bin/env bash

# 'source' this file to run tests

# if DJERBA_SOURCE_DIR not set
if [ -z "${DJERBA_SOURCE_DIR}" ]; then
    # set source dir based on script location; see https://stackoverflow.com/a/246128
    DJERBA_SOURCE_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/../.." &> /dev/null && pwd )
fi

# do sanity checking, then export the test variables
if [ ! -d "${DJERBA_SOURCE_DIR}" ]; then
    echo "DJERBA_SOURCE_DIR '$DJERBA_SOURCE_DIR' does not exist"
elif [ ! -d "${DJERBA_TEST_DIR}" ]; then
    echo "DJERBA_TEST_DIR '$DJERBA_TEST_DIR' does not exist"
elif [ -z "${DJERBA_BASE_DIR}" ]; then
    echo "Must load the Djerba environment module; first update MODULEPATH if necessary"
else
    # export variables for running tests on the source code
    export PYTHONPATH=${DJERBA_SOURCE_DIR}/src/lib:$PYTHONPATH
    export PATH=${DJERBA_SOURCE_DIR}/src/bin:$PATH
    export DJERBA_BASE_DIR=${DJERBA_SOURCE_DIR}/src/lib/djerba
    export DJERBA_RUN_DIR=${DJERBA_BASE_DIR}/util/data
    # DJERBA_TEST_DIR is set by the environment module
    export DJERBA_TEST_DATA=$DJERBA_TEST_DIR # deprecated, but still used in some tests
    # DJERBA_PRIVATE_DIR is set by the environment module
fi
