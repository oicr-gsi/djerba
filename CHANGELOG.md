# CHANGELOG

## Unreleased
### Added
- `review_status` field in Elba JSON output
- HTML documentation generated using [pdoc3](https://pdoc3.github.io/pdoc/).

## v0.0.1: 2020-10-08
Initial development release
### Added
- `djerba.py` script to run Djerba functions from the command line
- `djerba` Python package with modules to:
  - Validate Djerba config: `validate.py`
  - Construct genetic alteration output: `genetic_alteration.py`
  - Compute metric values: `metrics.py`
  - Contain sample attributes: `sample.py`
  - Write Elba config: `report.py`
  - Write cBioPortal files: `study.py`, `components.py`
- Tests for new modules, including:
  - Dry-run test of cBioPortal study/sample metadata
  - Live test of mutation output for cBioPortal & Elba, with MAF input
  - Test for dummy version of ShinyReport JSON output
- `setup.py` script for installation
- `prototypes` directory for metric code in development which is not production-ready
- Example JSON config for Elba: [elba_expected_mx.json](./src/test/data/elba_expected_mx.json)
