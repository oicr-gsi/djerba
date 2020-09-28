# djerba

Create reports from metadata and workflow output

## Introduction

Djerba is named for an [island](https://en.wikipedia.org/wiki/Djerba) off the coast of North Africa. It acts as a gateway between pipeline workflows and standard reporting formats.

Reporting formats supported by Janus include:
- JSON data structure for the OICR [ShinyReport](https://github.com/oicr-gsi/ShinyReport)
- Directory of data and metadata files for [cBioPortal](https://cbioportal.org/)

## Development plan

Janus development originated with the [cbioportal_tools](https://github.com/oicr-gsi/cbioportal_tools) project, which included creation of data folders for cBioPortal.

As of September 2020, the scope of Janus has been expanded to include ShinyReport. Relevant code from `cbioportal_tools` will be ported to the `janus` repository. Meanwhile, additional code will be developed to handle output for ShinyReport.

## Copyright and License

Copyright (C) 2020 by Genome Sequence Informatics, Ontario Institute for Cancer Research.

Licensed under the [GPL 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).
