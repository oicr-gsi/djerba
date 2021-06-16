#! /usr/bin/env bash

# This script is provided as an illustrative example of a Djerba test environment.
# Paths will likely need to be modified, to reflect Djerba file locations on the user's filesystem.
# After doing so, load the environment with `source test_env.sh`.
# Supplementary data can be validated using: src/test/ready_supplementary_data.py
# Python prerequisites have been installed in a virtual environment. See: https://docs.python.org/3/library/venv.html

source $HOME/oicr/workspace/venv/djerba/bin/activate
export PYTHONPATH=$HOME/oicr/git/djerba/src/lib:$PYTHONPATH
export PATH=$HOME/oicr/git/djerba/src/bin:$PATH
export DJERBA_TEST_DATA=$HOME/oicr/workspace/djerba/supplementary
export DJERBA_TEST_PROVENANCE=$HOME/oicr/workspace/djerba/modified_provenance/pass01_panx_provenance.modified.tsv.gz
# environment variable required for production, not just testing
export ONCOKB_TOKEN=/home/iain/oicr/workspace/resources/oncokb_api_token
