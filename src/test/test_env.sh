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
else
    # export variables for running tests on the source code
    export PYTHONPATH=${DJERBA_SOURCE_DIR}/src/lib:$PYTHONPATH
    export PATH=${DJERBA_SOURCE_DIR}/src/bin:$PATH
    export DJERBA_BASE_DIR=${DJERBA_SOURCE_DIR}/src/lib/djerba
    export DJERBA_RUN_DIR=${DJERBA_BASE_DIR}/data
fi
