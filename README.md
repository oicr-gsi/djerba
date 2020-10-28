# Djerba

Create reports from metadata and workflow output

## Introduction

Djerba translates cancer bioinformatics workflow outputs and metadata into standard reporting formats.

Formats supported by Djerba include:
- JSON data structure for the [Elba data review server](https://github.com/oicr-gsi/Elba)
- Directory of data and metadata files for [cBioPortal](https://cbioportal.org/)

Djerba is named for an [island](https://en.wikipedia.org/wiki/Djerba) off the coast of North Africa. (The initial letter D is silent, so it is pronounced "jerba".)

## Quick Start

Requires OICR [Modulator](https://gitlab.oicr.on.ca/ResearchIT/modulator).

- Load the Djerba environment module: `module load djerba`
- Run either of the two command-line scripts with `--help` for instructions:
  - `djerba.py`
  - `djerba_from_command.py`

## Documentation

The [doc](./doc/) directory holds additional documentation and examples, as described in its [README](./doc/README.md) file.

It includes [HTML documentation](./doc/html/djerba/index.html) of all classes and their attributes. The HTML was generated using [pdoc3](https://pdoc3.github.io/pdoc/); see 'Release Procedure' for details.

In addition, the `test` directory has a [README](./src/test/README.md) with details of tests and test data.

## Operation

### Prerequisites

- Python >= 3.7
- Python packages as listed in `setup.py`
- Python prerequisites are in the `djerba` environment module from OICR [Modulator](https://gitlab.oicr.on.ca/ResearchIT/modulator)
- OICR [Modulator](https://gitlab.oicr.on.ca/ResearchIT/modulator) environment modules required for cBioPortal `MUTATION_EXTENDED` output:
  - `vcf2maf/1.6.17`
  - `vep/92.0`
  - `vep-hg19-cache/92`
  - `hg19/p13`

### Testing

- Ensure prerequisites are available.
- Ensure test data at `/.mounts/labs/gsiprojects` is accessible (some dry-run tests can be run without this data)
- Check out the `djerba` repo: `git checkout git@github.com:oicr-gsi/djerba.git`
- Set the `PYTHONPATH` environment variable: `export PYTHONPATH=${MY_DJERBA_CHECKOUT_PATH}/src/lib:$PYTHONPATH`
- Run the test script: `./src/test/test.py`

### Installation

- Ensure prerequisites are available and tests pass.
- Ensure an up-to-date version of [pip](https://pypi.org/project/pip/) is available.
- From the repo directory, run `pip install .` to install using `setup.py`. This will copy `djerba.py` to the `bin` directory, and relevant modules and data files to the `lib` directory, under the installation path.
- See `pip install --help` for further installation options.

### Input Data

Input data types for Djerba are as follows:
- `MUTATION_EXTENDED`: Requires a MAF data file, and reference files in BED, TCGA and VCF formats.
- `CUSTOM_ANNOTATION`: This is a catch-all format, allowing arbitrary gene and sample annotation to be specified by the user in TSV files. See the [class documentation](./doc/html/djerba/genetic_alteration.html#djerba.genetic_alteration.custom_annotation) for details of input format.

### Running

There are two scripts to run Djerba:
- [djerba.py](./src/bin/djerba.py) is general-purpose, and requires a correctly formatted Djerba config file. It can be used to generate Elba config; generate a cBioPortal reporting directory; or validate Djerba config before running.
- [djerba_from_config.py](./src/bin/djerba_from_config.py) is a specialised script to generate Elba config from command-line arguments only, without the need for a config file.

Run either script with `--help` for a full description of command-line arguments and options.

## Development

### Conventions

- JSON example files should be formatted using `python -m json.tool` for consistency

### Repository Structure

- [src](./src): Production source code
- [src/bin/](./src/bin/): Scripts to run Djerba
- [src/lib/djerba](./src/lib/djerba): Python package for Djerba functions
- [src/test](./src/test): Tests for production code
- [prototypes](./prototypes): Development area for non-production scripts and tests

### Release Procedure

- Update `CHANGELOG.md`
- Increment the version number in `setup.py`
- Update HTML documentation by running: `pdoc --html djerba --force -o doc/html`. This requires (1) the [pdoc3](https://pdoc3.github.io/pdoc/) package; (2) an up-to-date version of the `djerba` package on the `PYTHONPATH`.
- Commit (or merge) to the master branch, and tag the release on Github
- Update environment module configuration in [OICR Modulator](https://gitlab.oicr.on.ca/ResearchIT/modulator) to install the newly tagged release

### Development History and Plans

Djerba development originated with the [cbioportal_tools](https://github.com/oicr-gsi/cbioportal_tools) project (also known as Janus). This included creation of data folders for cBioPortal.

As of September 2020, the scope of Djerba has expanded to include [Elba](https://github.com/oicr-gsi/Elba) (previously known as ShinyReport), a reporting tool developed at OICR. Input data and processing requirements for the two reporting types will overlap significantly, so they are to be handled by the same software repository.

Development progress is documented in [CHANGELOG.md](./CHANGELOG.md).

## Copyright and License

Copyright (C) 2020 by Genome Sequence Informatics, Ontario Institute for Cancer Research.

Licensed under the [GPL 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).
