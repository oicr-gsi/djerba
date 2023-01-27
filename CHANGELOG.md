# CHANGELOG

## Unreleased

### Added
- GCGI-587: Added CLIA number

### Fixed
- GCGI-698: Handle unknown cytoband without a misleading warning
- GCGI-702: Add apply/update cache options to benchmark script
- GCGI-703: Fix genome reference name in footer

## v0.3.19: 2023-01-13

### Fixed
- Fixes to margins & padding in CSS
- Removed hard-coded path in `test.py`

## v0.3.18: 2023-01-11

- Requires update to `djerba_test_data_lfs`

### GCGI-462: OncoKB annotation cache

- Documented in [oncokb_cache.md](./doc/oncokb_cache.md).
- `--apply-cache` and `--update-cache` options in `djerba.py`
- New script `update_oncokb_cache.py` for convenience/demonstration purposes
- Tests updated to use cached annotations
- Separate test for online OncoKB annotation; reduced input set for greater speed
- Modified tempdir setup in `extract` step; added `--no-cleanup` option to `djerba.py`

### GCGI-677: Update benchmark tests for Vidarr

- Update input glob for compatibility with Vidarr
- Updated test input data in `/.mounts/labs/CGI/gsi/djerba_test/`

## v0.3.17: 2023-01-03

### Changed
- GCGI-400: The config.ini parameter studyid now reflects the name of the study to be displayed in the report's case information section. A new parameter called projectid is used to reflect the project id as used by provenance (ie. to find files).
- GCGI-451: Assay version added to `.ini` settings, and assay name is assembled from assay version and `-w` and `-t` command line flags
- GCGI-612: Pipeline version added to `.ini` settings, and printed in report supplementary

## v0.3.16: 2022-12-21

### Fixed
- GCGI-665 Bugfix; stops OncoKB link generation from crashing on fusions
- Use OncoTree code, not TCGA code, to make OncoKB links
- Clean up `msi.txt` output to remove trailing tab character

## v0.3.15: 2022-12-20

### GCGI-403: CouchDB

#### Added
  - standalone scripts within folder > protoypes/db
  - addfolder.py: upload old reports from cluster
  - design.py & pull.py: query CouchDB and save as CSB and/or JSON
  - process.py: extact n number of gene/mutation from each sample
  - plots.rmd & plots.html: scatter and bar graphs
  - onco.rmd & onco.html: oncoplot from 3 graphs

#### Changed
  - location of JSON archive
  - edited archiver.py and render.py
  - replaced INI field archive_dir with archive_name ("djerba") and archive_url
  - created database.py that uploads to CouchDB via HTTP request
  - update test.py (archive_name is "djerba_test" for .ini's within test folder)

### GCGI-664 Sequenza file extraction bug

#### Fixed
  - Bug in which the `segments.txt` file for the wrong solution was extracted from the ZIP archive
  - `segments.txt` extraction made aware of multiple solutions
  - Renamed variables and added comments for greater clarity

### Other

  - Minor formatting fixes in `genomic_details_template.html` and `json_to_html.py`

## v0.3.14: 2022-12-13

- GCGI-642: minor changes to descriptive text in new format template

### Added
  - function to make percentiles as ordinal ('3' becomes '3rd') and add commas to large numbers (1000 because 1,000)
  - Arial was removed from CSS header because it wasn't necessary (and it was a HUGE chunk of base64); font configuration note added to README
  - oncokb levels are not printed in failed report supplementary
  - verb tense changed from present to past and INDEL changes to in/del
  - MSI description text was removed from supplementary (until MSI is validated)
  - GCGI-640: added MANE-select discription

## v0.3.13: 2022-12-06

- New report template. Now reporting TMB (GCGI-392) as actionable biomarkers. MSI and LOH calculated but not reported.

### Added
  - ammended report template added to prototypes
  - QC report prints as '${requisition}_qc'
  - 'biomarkers_plot' R script for plotting MSI score (and future biomarkers)
  - added 'cnv_plot.R' and 'pga_plot.R' for visualization of CNVs and PGA, respectively, in new report format
  - new R function 'preProcLOH' calculates LOH on the per gene basis from the aratio_segment.txt file
  - new 'centromeres.txt' file in data directory for position of centromeres in CNV plot
  - new 'pgacomp-tcga.txt' file in data directory for distribution of PGA across the TCGA cohort
  - MSI and 'aratio_segment.txt' file preprocessing in 'r_script_wrapper.py'
  - annotation of LOH, MSI-H and TMB-H by Oncokb in 'report_to_json'
  - added colour to oncokb levels using process_oncokb_colours function in 'json_to_html' and corresponding CSS

### Changed
  - Updated TMB plotting script to show TMB-High cutoff
  - 'vaf_plot.R' format adjusted and slimmed
  - Updated  'configure.py' and 'provenance_reader' to find msisensor files and segment.txt files
  - Architecture of report template:
    - integrated and moved all CSS to new 'style.css' file
    - moved definitions and descriptions to subdirectory called 'templates_for_supp'
    - moved footer template to 'supplementary_materials_template.html'
  - body of clinical report changed to a two-cell layout, with title on left and info on right, resulting in changes to several .html/mako file, and new function 'make_sections_into_cells' in 'json_to_html'
  - changed table style in 'json_to_html.py' into two columns per sample information, with corresponding CSS that bolds the sample info title
  - split WGS and WTS assay descriptions into seperate description files, added WTS DNA extraction protocol info, added links to all software in description as well as to hg38
  - changed definitions_1 and definitions_2 to definitions_metrics and definitions_tests which are for sample QC metric descriptions and biomarkers respectively
  - renamed 'genomic_therapies_template.html' to 'therapies_template.html' to avoid confusion with 'genomic_details_template.html'
  - pdf footer prints title left
  - GCGI-396: arial font as base64 in CSS file makes pdf renderable on the cluster
  - GCGI-440, GCGI-593: TCGA replaced by oncotree in URL links
  - GCGI-585: getting rid of div container around entire report made page-breaks controlable
  - GCGI-586: allowing cluster pdf printing locks in page numbering
  - GCGI-587: CLIA added to report header
  - GCGI-588: hg38 patch added to footer

## v0.3.12: 2022-11-23

- Requires update to `djerba_test_data_lfs`

### Added
- GCGI-517 New 'requisition ID' INI parameter; use for report title

### Fixed
- GCGI-423 Include `-q` option for MAF annotation script
- GCGI-608 Do not write 'technical notes' text box unless it has non-null content


## v0.3.11: 2022-11-01

### Changed
- GCGI-516 Change default file provenance report path to Vidarr
- Updated to use Python Tools module v16 for Geneticist Review Report

## v0.3.10: 2022-10-25

### Added
- GCGI-422 Add a 'technical notes' section to the report; includes update to djerba_test_data_lfs

### Changed
- GCGI-506 Increase test speed by using custom file provenance throughout

### Fixed
- GCGI-509 Correctly find MAF file in provenance

## v0.3.9: 2022-10-12

### Changed
- GCGI-384 Fixed CNV vs Small mutation mismatch

## v0.3.8: 2022-10-12

### Changed
- GCGI-495 Support for Vidarr workflow names
- Updated to use Python Tools module v15 for Geneticist Review Report

## v0.3.7: 2022-09-29

### Changed

- GCGI-496 Expand list of permitted variant types in MAF
- Updated README and added a diagram of Djerba structure

### Fixed
- GCGI-494 Fix input column header in `vaf_plot.R`
- GCGI-496 Fix FILTER column evaluation for MAF
- Fixed typo in `test_env.sh`

## v0.3.6: 2022-09-22

### Changed
- GCGI-461: Refactor OncoKB annotation into a separate class
- GCGI-479: Update to use oncokb-annotator version 3.3.1

### Fixed

- GCGI-480: Bugfix for `djerba.py` crash in `extract` mode
- Fixes to `test_env.sh` script

## v0.3.5: 2022-08-30

### Fixed

- GCGI-449: Fix for `delly` regex in provenance reader

## v0.3.4: 2022-08-18

### Added

- GCGI-414: Support for multiple requisitions from one donor

### Changed

- GCGI-430: Update Mutect2 version to GATK 4.2.6.1
- Move Djerba version text into assay description section

### Fixed

- GCGI-442: Remove delly results from JSON and HTML

## v0.3.3: 2022-07-25

### Changed

- GCGI-200: Record Djerba software version in report footer and log
- GCGI-390: Change plot output from JPEG to SVG
- GCGI-404: Restructure test data; update `test_env.sh`; move GSICAPBENCH tests to separate file
- Updated to use Python Tools module v12 for Geneticist Review Report

### Fixed

- GCGI-387: Enforce decimal places in output for purity, ploidy, coverage, callability
- GCGI-399: Rename "Genome Altered (%)" to "Percent Genome Altered"
- GCGI-406: Do not compare supplementary data in benchmark script
- GCGI-416: Do not allow 'None' in default tumour/normal IDs
- GCGI-417: Add missing gene names in allCuratedGenes.tsv

## v0.3.2: 2022-06-21

### Fixed

- GCGI-398: Sort variant tables by cytoband
- GCGI-401: Remove obsolete script check
- GCGI-402: Check for Mavis inputs

## v0.3.1: 2022-06-17

### Added
- GCGI-380: Add convenience scripts to update/view JSON

### Fixed
- GCGI-379: Mavis job ID fix; remove `wait_for_mavis.py`; decode stdout/stderr from subprocesses
- GCGI-381: Permissions on executable scripts
- GCGI-382: Fix handling of unknown TCGA codes
- GCGI-386: Display VAF as percentage, not decimal
- GCGI-391: Add "Inconclusive" to list of known OncoKB levels

## v0.3.0: 2022-06-08

### Added
- Introduces a main JSON document, with all information needed to generate a report
- GCGI-197 Assay title in QC table
- GCGI-270 Italicize gene names in Supplementary Gene Information
- GCGI-291 Replace Rmarkdown with Mako template
- GCGI-292 Run in wgs-only and failed modes without Mavis input
- GCGI-326 Standardize report filenames
- GCGI-328 Automated generation of benchmark reports
- GCGI-353 Support markdown in genomic summary
- GCGI-367 New `ASSAY_NAME` parameter in INI
- Default HTML names and PDF names conform to convention
- `subprocess_runner` class to run commands and log the results

### Fixed
- GCGI-268 Make clinical and QC report filenames consistent
- GCGI-312 Correctly populate Study and Oncotree in the report
- GCGI-359 Update VEP version in footers
- GCGI-365 Improved page breaks in PDF
- GCGI-374 Report purity as a percentage
- GCGI-375 Filter small mutations & indels by variant classification

## v0.2.9: 2022-05-16

### Fixed
- GCGI-368: Apply colour update to WGS-only TMB plot

## v0.2.8: 2022-05-09

### Changed
- GCGI-359 Update VEP version number in report footers

## v0.2.7: 2022-05-03

### Fixed
- GCGI-354 Update MAF filter to retain `clustered_events;common_variant`

## v0.2.6: 2022-04-28

### Fixed
- GCGI-352 Correctly process new MAF column indices
- GCGI-353 Fix purity/ploidy message

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
