# Djerba

Create reports from metadata and workflow output

## Introduction

Djerba translates workflow outputs and metadata into standard reporting formats. Input is metadata and workflow results specified in a JSON config file; output is one or more report files.

Reporting formats supported by Djerba include:
- JSON data structure for the [Elba data review server](https://github.com/oicr-gsi/Elba)
- Directory of data and metadata files for [cBioPortal](https://cbioportal.org/)

Djerba is named for an [island](https://en.wikipedia.org/wiki/Djerba) off the coast of North Africa. (The initial letter D is silent, so it is pronounced "jerba".)

## Operation

### Prerequisites

- Python >= 3.7
- Python packages as listed in `setup.py`
- OICR [Modulator](https://gitlab.oicr.on.ca/ResearchIT/modulator) environment modules required for cBioPortal `MUTATION_EXTENDED` output:
  - vcf2maf/1.6.17
  - vep/92.0
  - vep-hg19-cache/92
  - hg19/p13

### Testing

- Ensure prerequisites listed above are available
- Ensure test data at `/.mounts/labs/gsiprojects` is accessible (some dry-run tests can be run without this data)
- Check out the `djerba` repo: `git checkout git@github.com:oicr-gsi/djerba.git`
- Set the `PYTHONPATH` environment variable: `export PYTHONPATH=${MY_DJERBA_CHECKOUT_PATH}/src/lib:$PYTHONPATH`
- Run the test script: `./src/test/test.py`

### Installation

- Ensure prerequisites are available and tests pass.
- Ensure an up-to-date version of [pip](https://pypi.org/project/pip/) is available.
- From the repo directory, run `pip install .` to install using `setup.py`. This will copy `djerba.py` to the `bin` directory, and relevant modules and data files to the `lib` directory, under the installation path.
- See `pip install --help` for further installation options.

### Running

The [djerba.py](./src/bin/djerba.py) script is the main method of running Djerba. Run with `--help` for a full description of command-line options.

The script requires a config file in JSON format; it validates the file against a [JSON schema](https://json-schema.org/) before proceeding. The config schema is [input_schema.json](src/lib/djerba/data/input_schema.json). Example config files are in [src/test/data](src/test/data).

`djerba.py` has three modes of operation:
- `elba`: Write a JSON config file for Elba, for a given sample
- `cbioportal`: Write a study directory for upload to a cBioPortal instance, for multiple samples
- `validate`: Validate a Djerba config file and report any errors

## Repository structure

- [src](./src): Production source code
- [src/bin/djerba.py](./src/bin/djerba.py): Main script to run Djerba
- [src/lib/djerba](./src/lib/djerba): Python package for Djerba functions
- [src/test](./src/test): Tests for production code
- [prototypes](./prototypes): Development area for non-production scripts and tests

## Development History and Plans

Djerba development originated with the [cbioportal_tools](https://github.com/oicr-gsi/cbioportal_tools) project (also known as Janus). This included creation of data folders for cBioPortal.

As of September 2020, the scope of Djerba has expanded to include ShinyReport. Relevant code from `cbioportal_tools` will be ported to the `djerba` repository and further developed to support cBopPortal. Meanwhile, additional code will be developed to handle output for ShinyReport.

Development progress is documented in [CHANGELOG.md](./CHANGELOG.md).

## Copyright and License

Copyright (C) 2020 by Genome Sequence Informatics, Ontario Institute for Cancer Research.

Licensed under the [GPL 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).
