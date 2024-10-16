#!/bin/bash
set -e
docker build -t djerba .
docker run -t  -v `pwd`:`pwd` -w `pwd` --rm djerba "$@"
