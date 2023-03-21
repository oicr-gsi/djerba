#! /usr/bin/env python3

import json
import jsonschema
import logging
import os
import sys

sys.path.pop(0) # do not import from script directory
from djerba.core.json_validator import json_validator

USAGE = "Usage: Input on STDIN, eg. `validate.py < /home/foo/config.json`"

def main():
    if sys.stdin.isatty():
        print("Input must be non-empty", USAGE, sep="\n", file=sys.stderr)
        sys.exit(1)
    validator = json_validator(log_level=logging.INFO)
    validator.validate_string(sys.stdin.read())

if __name__ == '__main__':
    if len(sys.argv)>1:
        print(USAGE, file=sys.stderr)
        sys.exit(1)
    main()
