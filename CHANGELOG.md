# CHANGELOG

## v0.2.5: 2022-03-28

### Fixed
- GCGI-333 Bugfix for cancer type description

## v0.2.4: 2022-03-23

### Fixed
- GCGI-331 Standardize on --study for script options
- GCGI-332 Remove read threshold filter from Mavis

## v0.2.3: 2022-03-18

### Fixed
- GCGI-323 Correctly handle missing `geo_tube_id` value

## v0.2.2: 2022-03-09

### Changed
- GCGI-311 Reformat the genomic landscape table
- GCGI-312 Better placeholder text for Study ID and Oncotree Code

## v0.2.1: 2022-02-24

### Fixed
- GCGI-294 Correct handling of --failed option for all script modes

## v0.2.0: 2022-02-22

### Added
- GCGI-250 Add --wgs-only option for HTML reports
- GCGI-269 Script `list_inputs.py` to list report input paths
- GCGI-201 Documentation for OncoKB file updates

### Changed
- GCGI-265 Omit processing of unnecessary inputs for failed reports
- GCGI-266 Update failed report markdown to incorporate recent changes from CGI-Tools
- GCGI-271 Failed report formatting change
- GCGI-272 Update target coverage explanation in footers
- Update color handling for plotting in Rmarkdown
- Updated to use Python Tools module v12 for Geneticist Review Report

### Fixed
- GCGI-289 Fix for fallback ID creation

## v0.1.0: 2022-01-28

No code changes from v0.0.17; version incremented for first production release

## v0.0.17: 2022-01-26

### Added
- GCGI-264 Add --legacy option to run CGI-Tools legacy Mavis

### Fixed
- GCGI-262 Additional fixes for Mavis inputs
- Add req_approved_date to config.ini template

## v0.0.16: 2022-01-21

### Fixed
- GCGI-262 Fix for Mavis inputs

## v0.0.15: 2022-01-18

### Fixed
- GCGI-257 Fix for Rmarkdown error

## v0.0.14: 2022-01-14

### Added
- GCGI-256 Correctly process samples with empty fusion data after filtering

### Fixed
- GCGI-255 Fix in release v0.0.13 was incorrect; rectified in this release

## v0.0.13: 2022-01-12

### Fixed
- GCGI-255 Correct index for gene ID in GEP input

## v0.0.12: 2021-12-14

## Changed
- GCGI-241 Remove the concept of an analysis unit; enables Djerba to work with V2 aliases in MISO
- GCGI-247 Update the QC report shell script and improve dependency handling

### Fixed
- GCGI-244 Launch Mavis with hg38 instead of hg19

## v0.0.11: 2021-11-11

### Fixed
- GCGI-234 Add delly and arriba inputs to Mavis launch script

## v0.0.10: 2021-10-25

### Added
- GCGI-231 New INI field for requisition approved date

## v0.0.9: 2021-10-22

### Added
- GCGI-229 Add external dataset plotting function

### Fixed
- GCGI-224 HTML template improvements
- Copy Rmarkdown script and associated files into tempdir, to allow writing to script directory
- Remove unnecessary import from test

## v0.0.8: 2021-10-21

### Added
- GCGI-230: Add the QC report shell script

### Changed
- GCGI-226: Use double colon :: as fusion gene separator

## v0.0.8b: 2021-10-07

- Bugfix for paths in setup.py

## v0.0.8a: 2021-10-07

- Pre-release to check an HTML rendering bug
- Fixes GCGI-221

## v0.0.7: 2021-09-30

- Implements extra features required to fully replace CGI-Tools
- Release for validation of SOP update

### Added
- `html2pdf.py` convenience script
- GCGI-186: Setup mode in main script
- GCGI-187: Fail and target-coverage options for HTML generation
- GCGI-189: Script option to locate Sequenza results in file provenance
- GCGI-190: Script to manually run Mavis
- GCGI-191: Record Sequenza reviewer names
- GCGI-192: Add logR cutoff calculation
- GCGI-194: Automatically archive INI files
- GCGI-216: Replace CGI_PLACEHOLDER in report footer

### Fixed
- GCGI-193: Sequenza configuration/metadata fixes
- GCGI-205: Fix for Sequenza reader on alternate solutions
- GCGI-212: Refactor PDF command line arguments

### Changed
- GCGI-215: Rename basedir variable
- GCGI-217: Add a --pdf option to HTML mode

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
