# CHANGELOG

## Unreleased
- GCGI-186: Setup mode in main script
- GCGI-187: Fail and target-coverage options for HTML generation
- GCGI-189: Script option to locate Sequenza results in file provenance
- GCGI-190: Script to manually run Mavis
- GCGI-193: Sequenza configuration/metadata fixes
- GCGI-194: Automatically archive INI files

## v0.0.6: 2021-08-19

- Patch release for a misnamed variable in main.py.

## v0.0.5: 2021-08-17

- Release for final testing and validation before going into production
- Improved logging and testing
- Additional features to enable Djerba to replace CGI-Tools

### Added
- GCGI-173: Logging for Djerba
- GCGI-174: Report min/max purity in gamma selector
- GCGI-175: INI documentation and validation
- GCGI-176: Prototype JSON summary output
- GCGI-177: Clean up and document Djerba test data; make tests portable
- GCGI-178: Automatically discover tumour/normal/patient ID and OncoTree data
- GCGI-180: PDF generation with wkhtmltopdf
- GCGI-182: Generate the "analysis unit" string for the final PDF report
- GCGI-184: Miscellaneous small fixes

## v0.0.5a: 2021-07-07
- Alpha release of a new version of Djerba, for generating CGI reports only
- For initial testing and evaluation only; *not* intended for production
- Installed and run successfully for the svc.cgiprod user

## v0.0.4: 2021-06-09
- Work-in-progress on features for the old Djerba design.
- To be replaced by a simplified Djerba handling CGI reports only, in release 0.0.5.
### Added
- GCGI-27: Upload config to Elba server
  - Standalone script `upload.py`
  - Upload options added to `djerba_from_command.py`
  - New `uploader` class as parent of `report`
- GCGI-30: Expand MAF processing to populate the following fields:
  - `Gene`
  - `Chromosome`
  - `Protein_Change`
  - `Allele_Fraction_Percentile`
  - `FDA_Approved_Treatment`
  - `OncoKB`
  - `Variant_Reads_And_Total Reads`
  - `TMB_PER_MB`
  - `COSMIC_SIGS`: Placeholder only
- GCGI-67: Input data from SEG files for the FRACTION_GENOME_ALTERED metric
- GCGI-89: Consistency checks on metric inputs
  - Error if a sample/gene attribute has a non-null value in more than one input source
  - Refactoring and simplification of unit tests
  - Reformat JSON files using `json.tool` in Python

## v0.0.3: 2020-11-10
### Added
- GCGI-55: Test Elba JSON output against the schema
- GCGI-62: Add Oncogenic_Binary to Elba config schema
- GCGI-63: Additional fields in Elba config schema

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
