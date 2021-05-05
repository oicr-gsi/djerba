#! /usr/bin/env python

# Simplified djerba script for CGI reports only
# - supply input config
# - read inputs
# - collate results; transform from input-major to gene-major order
# - write JSON output

import argparse

import djerba.simple.builder

