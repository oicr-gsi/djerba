# CHANGELOG

## v0.0.2: 2020-10-28
### Added
- `review_status` field in Elba JSON output
- HTML documentation generated using [pdoc3](https://pdoc3.github.io/pdoc/).
- GCGI-36: Custom annotation in TSV format with the `custom_annotation` class.
- GCGI-45: Script `djerba_from_command.py` to generate Elba JSON from command-line arguments
### Removed
- `genetic_alteration_demo` class
### Changed
- GCGI-39: Update JSON schema, example files and documentation. Much more detail added to Djerba config schema.
- GCGI-54: Updated example JSON output with fields for `MutationClass`, `Fusion` and `Variant_Classification`
- `genetic_alteration` is no longer a subclass of `dual_output_component`
- `validate.py` renamed to `config.py` and includes a new `builder` class

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
