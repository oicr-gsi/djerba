# CHANGELOG

## Unreleased

### WGS 4.0

- Removed file list in expression data
- added HRD to genomic landscape
- GCGI-1173: genomic landscape plugin uses provenance_helper
- GCGI-1220: fixed MSI table formatting
- GCGI-1190: Removed obsolete data values/files
- GCGI-1012: Moved R testing to formal tests
- GCGI-1304: Merge updates to genomic landscape plugin and resolve conflicts
- GCGI-1319: Update genomic landscape plugin to read purity from PURPLE output file
- new PURPLE CNV calling plugin
- removed sequenza support
- new `djerba.plugins.wgts.common` package for code shared between multiple WGTS/WGS plugins
- Added "r" directory to setup, bug fix (metrix_cell -> metric_cell)
- Added ARID2 to SWI/SNF gene list in CAPTIV8 plugin
- Removed copy state from SNVs and Indels plugin
- Added LOH to SNVs and Indels plugin

### External plugin support

- GCGI-993: Support for plugins outwith the main `djerba` package

### Other

- GCGI-1257: Fix import of traceback module
- GCGI-1313: Refactor reading input_params.json
- GCGI-1322: Warning instead of error if manually configured sample name does not match provenance
- GCGI-1323: Support PWGS in mini-Djerba by making summary optional
- GCGI-1325: Rewrite case_overview config method to fix bugs and make it clearer
- GCGI-1344: Write updated JSON by default, with a more informative name

## v1.5.5: 2024-03-05
- Further fixes to pWGS Cardea helper to allow multiple projects for one donor

## v1.5.4: 2024-03-01

- Fixed pWGS Cardea helper, pWGS provenance helper

## v1.5.3: 2024-02-22

- GCGI-1280: Allow `wgts.snv_indel` plugin to run as standalone
- Enable fallback values when updating null parameters from JSON

## v1.5.2: 2024-02-20

- GCGI-1299: Redact gene descriptions in benchmark comparison
- GCGI-1301: Add report title and patient info to benchmark INI

## v1.5.1: 2024-02-15

- GCGI-1296: Remove unwanted backslash and correctly insert configured sign-off date

## v1.5.0: 2024-02-13

### Report reformatting
- GCGI-1266: moved clinical footer into supplement plugin
- supplement.header plugin removed
- added Geneticist INI parameter to appendix
- GCGI-1294: Support new supplement.body params in mini-Djerba

### Benchmark and test improvements
- GCGI-1253: Fix JSON equivalence check and add tests
- GCGI-1292: Add OncoKB caching to `genomic_landscape` plugin
- Update `test_env.sh`
- Add convenience scripts to run tests: `run_all_tests.sh`, `run_quick_tests.sh`

### Update mode bugfix
- GCGI-1291: Do not overwrite previous JSON before generating updated report

### Minor cleanup actions
- GCGI-1287: Remove obsolete data files
- GCGI-1267: Fix copyright date in README

## v1.4.1: 2024-02-02

- fix bug when fusions have multiple possible reading frames
- GCGI-1251: replaced and automated test dir variables

## v1.4.0: 2024-01-31

- GCGI-611: fix fusion frameshift hardcode
- GCGI-443: merge duplicate fusion rows
- fixed bug removing oncogenic fusions
- GCGI-1217: Remove NORMAL_DEPTH variable
- GCGI-1194: Research Report PDF Footer says RUO
- GCGI-1261: Update plugin tester base class, so it is unaffected by changes in core HTML
- removed "Quality Failure" text in failed report plugin html
- GCGI-1282: fixed config generation for pWGS in setup mode, and removed automatic generation of failed report sentence
- GCGI-1278: Fix issues with fusion plugin in benchmark tests; update `test_env.sh`; add convenience test scripts

### Improvements for mini-Djerba

- GCGI-1265: Automatically fill in report dates (preserving date of original report draft)
- GCGI-1268: Use report ID for name of JSON output file
- GCGI-1269: Default to user-friendly minimal error text
- GCGI-1270: `--version` option in `djerba.py` and mini-Djerba
- GCGI-1271: Mini-Djerba modes changed to setup/render/update

## v1.3.1: 2024-01-19

- Fixed support for 40X assay
- GCGI-1186: Remove `mavis.py`
- GCGI-1258: Fix import in args processor base
- GCGI-1264: Rename mini-djerba link

## v1.3.0: 2024-01-16

- Mini-Djerba: Lightweight application to update patient info/summary in existing reports
- MDC file format: Mini-Djerba Config, with file extension .mdc
- New `report_title` plugin
- Added annotation of translocations eg t(11;14)
- Fixed issue with reading summary text path (GCGI-1256)

## v1.2.1: 2024-01-12

- Fixes for clinical report header and installation of patient_info plugin

## v1.2.0: 2024-01-11

- Add a `patient_info` plugin
- Add `update` mode to the main Djerba script, to update and render an existing JSON file
- New features are a proof-of-concept for enabling the geneticist to edit reports with a portable mini-Djerba
- Removed the `update_oncokb_cache.py` script; replaced by `djerba.py update --summary=...`
- Addition of `pwgs_cardea_helper` to pull sample info using a requisition ID

## v.1.1.3: 2024-01-10

- Fixed unit tests for supplements plugin

## v.1.1.2: 2024-01-08

- GCGI-1233: allowed support for purity and ploidy to be "NA", changed failed report template text
- Fixed unit tests for various plugins
- Changed sign-offs page break to "auto"
- GCGI-1240/1241: added filtering for 2 TERT hotspots: -124bp G>A and -146bp G>A

## v1.1.1: 2023-12-13

- Fixed template text for failed plugin
- Added plugins missing from `setup.py`
- GCGI-1229: Fixed missing OncoKB definitions

## v1.1.0: 2023-12-08

- Removed `prototype` directory, which is now in the [djerba_prototypes](https://github.com/oicr-gsi/djerba_prototypes) repo
- Added RUO-report functionality
- Added HRD plugin to RUO report
- Split pWGS-sample plugin into three plugins
- Created CAPTIV-8 plugin
- Added Djerba core version to JSON output
- Updated and fixed unit tests which were omitted for release 1.0.0
- Updated benchmarking functions which were omitted for release 1.0.0

## v1.0.3: 2023-11-28

- Allow tumour ID to be specified in the sample plugin
- GCGI-1191: fixed MSI suffix from .filter.deduped.realigned.recalibrated.msi.booted to .recalibrated.msi.booted

## v1.0.2: 2023-11-20

- GCGI-1172: TCGA code throws error when lower-case
- GCGI-1174: Add `[genomic_landscape]` to setup mode
- GCGI-1175: Pipeline version in supplementary
- GCGI-1177: Fix execution order of expression helper
- GCGI-1182: Fix Whizbam links. New INI parameter `whizbam_project` in `snv_indel`.
- GCGI-1183: Update Gene Information file

## v1.0.1: 2023-11-14

- GCGI-612: Remove hardcoded cfDNA in TAR plugin; add `sample_type` parameter
- GCGI-1166: Fix for new workflow names
- GCGI-1167: Fix for unknown cytoband names

## v1.0.0: 2023-11-03

- First production release of new plugin-based Djerba
- Other than version number, code is identical to `v1.0.0-dev0.0.23`

## v1.0.0-dev0.0.23: 2023-11-03

### GCGI-1125
- Update core tests

## v1.0.0-dev0.0.22: 2023-11-03

### GCGI-1155
- Do not auto-generate the date in PDF page footer; use yyyy/mm/dd placeholder instead

### GCGI-1154
- Ensure therapies for the same gene with different OncoKB levels are distinct

## v1.0.0-dev0.0.21: 2023-11-01

### GCGI-1153
- Fix syntax errors in assay selection for setup

## v1.0.0-dev0.0.20: 2023-11-01

### GCGI-1147
- Generate URL after updating BRAF protein name

### GCGI-1128
- SNV filtering bugfix

### Other
- Update README
- Additional options in setup
- Priority fix for failed report plugin
- Date in report sign-off
- Add OncoKB links for actionable CNVs

## v1.0.0-dev0.0.19: 2023-10-31

### GCGI-1146
- OncoKB links for CNVs in therapy tables

### GCGI-1145
- Automatically fill in current date in report author line of sign-offs

### GCGI-1144
- Exclude mutations rated below Likely Oncogenic (including Inconclusive) from CNV gene info

### GCGI-1128
- Exclude 5'Flank mutations (other than TERT) when filtering MAF

## v1.0.0-dev0.0.18: 2023-10-30

### GCGI-1143
- Removed extra break-end in 'Definitions', before 'Expression Percentile'
- Removed 'genes tested' from disclaimer
- Changed report ID to be tumour ID + version only

### GCGI-1142
- Removed any building of gene info from genomic landscape plugin

### GCGI-1129
- Only report fusion genes if rated Likely Oncogenic or higher

### GCGI-1130
- Fix order of columns in snv/indel table

## v1.0.0-dev0.0.17: 2023-10-30

### GCGI-1132: Provenance helper fixes
- Add discovered INI parameters for tumour ID and normal ID
- Ensure `sample_info.json` is consistent with manual INI configuration
- Handle missing `input_params.json` without crashing
- Do not rewrite provenance subset at config step, if file is already present

## v1.0.0-dev0.0.16: 2023-10-27
- Add genomic landscape plugin to `setup.py`

## v1.0.0-dev0.0.15: 2023-10-26

### GCGI-1127: Genomic Landscape AttributeError
- Fixed AttibuteError in genomic landscape plugin

## v1.0.0-dev0.0.14: 2023-10-26
- Fix for missing `__init__.py`

## v1.0.0-dev0.0.13: 2023-10-26

### GCGI-1118, GCGI-1120
- Delete obsolete code
- Temporarily disable `benchmark.py` script

### GCGI-1124
- Enable `setup` mode in `djerba.py` to generate an INI file
- Fixed config omissions in fusion plugin and expression helper
- Move `update_wrapper_if_null` method to `configurable` class

### GCGI-1116
- Make a new `djerba.util.directory_finder` class
- Use it to replace various ad hoc methods for finding directories from environment vars

### GCGI-1122
- Output placeholder values

### GCGI-1123: Gene information threshold
- Correct reporting threshold for gene information merger in the CNV and SNV/indel plugins

### GCGI-836: Enable archiving
- Enable archiving to CouchDB
- Simplify previous archiving code; get rid of `archiver.py` and just use `database.py`
- Fixes to POST operation to update existing documents; now confirmed as working

### GCGI-1113: System integration
- Minor bugfixes to allow successful generation of integrated report
- Split supplementary plugin into `body` and (extremely simple) `header` plugins
- New `supplement.header` plugin allows exact control of header location
- Update default priorities for correct rendering order in WGTS report
- Warn if default author name is in use; OK for testing, not allowed in production
- Automatically discover sequenza path, oncotree code, tumour id in `cnv` plugin
- Further simplification of INI parameters for `cnv` and `snv_indel` plugins
- Check purity is consistent between `input_params_helper` and `cnv` plugin
- Validation checks on `input_params_helper` config values

## v1.0.0-dev0.0.12: 2023-10-19

### GCGI-1114: Fix for tar plugin install
- Add `djerba.plugins.tar.snv_indel.snv_indel_tools` to `setup.py`

### GCGI-1108: Remove djerba.render dependencies
- Remove dependencies on obsolete files
- Concludes work started in GCGI-1070
- Corrects path to `gencode_v33_hg38_genes.bed`

### GCGI-1070: Delete obsolete files
- Delete obsolete files from Djerba classic
- Temporary reprieve for files in `render` still in use by plugins

### GCGI-1091: Record extraction time in core JSON
- Record the extraction time in UTC for later reference

### Fixed
- Fix logging bug for check on author name

## v1.0.0-dev0.0.11: 2023-10-17

### GCGI-1106: Update setup
- Update `setup.py` to correctly install data files
- Installation must include core, plugins, helpers, mergers
- Also updated dependencies in `setup.py`
- GCGI-993 will handle this in a decentralized way, but is out of scope for v1.0.0

### GCGI-1083: SNV and CNV updates
- Rework the draft SNV/indel plugin to make it production ready

## v1.0.0-dev0.0.10: 2023-10-17

### GCGI-1105: Add initializer to directories
- Added __init__.py files to directories where it was missing

## v1.0.0-dev0.0.9: 2023-10-16

### GCGI-1083: SNV and CNV updates
- Rework the draft CNV plugin to make it production ready

### GCGI-1077: Merger JSON factories
- Add factory classes to generate correct JSON for mergers; use in the fusion plugin

### GCGI-1076: Gene information merger update
- Add a Mako template to render correctly formatted HTML

### GCGI-819: Fusions plugin
- Plugin to generate 'Structural Variants and Fusions' section of report

### GCGI-1075: Provenance helper update
- Write a `path_info.json` file to the workspace
- Contains commonly used paths for use by other plugins/helpers

### GCGI-1071: Expression helper
- Helper class to compute gene expression levels from RSEM results

### GCGI-1035: Treatment options merger
- Generate the "Treatment Options" section of the report
- Include both "FDA Approved" and "Investigational Therapies"

## v0.4.17: 2023-09-18

- Replaced splice site annotation with `Truncating Mutations` in OncoKB links for splice site mutations

## v0.4.16: 2023-09-12

- GCGI-1042: Changes to verb tense in genomic summary templated text
- GCGI-1032: Reference cohort name is uppercase and adds TCGA when it is TCGA

## v0.4.15: 2023-09-06

- GCGI-1063: Redact TMB genomic biomarker plot from benchmark comparison

## v0.4.14: 2023-08-17

- GCGI-1030: Fix glob pattern for Sequenza results in benchmarking

## v1.0.0-dev0.0.8: 2023-08-11

### GCGI-963: Case overview plugin
- Renamed the patient info plugin
- Brought up to date with new display format from master
- Now supports WGTS, WGS, and TAR

### GCGI-1016: Default working directory
- Make `--work-dir` optional in `djerba.py` script; defaults to the output dir

### Other
- In clinical report footer, added "Report Sign-Offs" heading and removed auto-generation of the date
- Added `summary` plugin to generate the genomic summary text
- Added `supplement` plugin to generate supplementary info (definitions, software versions, etc.)

## v1.0.0-dev0.0.7: 2023-08-02

### GCGI-963: Patient info plugin
- Simple plugin to generate the Clinical Research Report header and Case Overview section

### GCGI-982: Provenance helper update
- Update to complement changes to core functionality
- Writes subset of provenance and `sample_info.json` at both configure and extract


## v0.4.13: 2023-07-31

### Changed
- GCGI-989: Made adjustments to biomarker plots
- GCGI-1011: Update to find new sequenza file path

### Added
- example .pdf and .ini of WGTS report in `examples/`

## v0.4.12: 2023-07-19

### Changed
- GCGI-956: The TMB plot has been moved to a linear format and the PGA plot has been removed

### Added
- GCGI-957: The number of candidate SNVs for the pWGS assay are listed in Genomic Landscape section

## v0.4.11: 2023-06-27

### Changed
- GCGI-864: removed annotation of 5'UTR, 3'UTR, and 3'Flank. 5'Flank only annotated if TERT
- Sample QC results moved to below summary
- Split some `Case Overview` section into a new `Patient and Physician` section
- Removed tracking of patient's genetic sex
- GCGI-943: Overrode HGVSp for BRAF V640E to be represented as V600E
- GCGI-942: Changed expected maf file extension from '.filter.deduped.realigned.recalibrated.mutect2.filtered.maf.gz' to '.mutect2.filtered.maf.gz'

## v0.4.10: 2023-06-06

### Changed
- ACD -> ACDx
- Added "-" between date and report name in footer
- GCGI-806: Modify `benchmark.py` interface; remove `--compare-all` option; add `--delta` argument for permitted difference in expression levels

### Fixed
- GCGI-870: Fix for biomarker annotation cache; required for benchmark cron

## v0.4.13: 2023-07-31

### Changed
- GCGI-989: Made adjustments to biomarker plots
- GCGI-1011: Update to find new sequenza file path

### Added
- example .pdf and .ini of WGTS report in `examples/`

## v1.0.0-dev0.0.6: 2023-07-20

### GCGI-967: Overhaul core functionality
- Define core INI parameters and implement in `core_configurer`
- Get rid of placeholder data at the core extract step
- Add PDF rendering to the core
- Introduce `document_config.json` with settings to render HTML
- Render multiple HTML/PDF documents, identified by attributes (clinical, research, etc)
- Add a `mako_renderer` utility class with tests

### GCGI-950: Attributes
- Represent attributes as a comma-separated list, instead of individual parameters
- Add a method to check all attributes are known
- Define a list of known attributes in `configurable` class; may override in subclasses

### GCGI-951: Dependencies
- Explicitly represent plugin dependencies with INI parameters
- Params `depends_configure` and `depends_extract` expect a comma-separated list of component names, which will be checked at runtime
- Do not define a dependency param at the render step; JSON output from each plugin is expected to be self-contained, so all dependencies should be resolved at the extract step.

### GCGI-955: `specify_params`
- Each plugin must have a `specify_params` method to define required and optional INI parameters
- Using an INI parameter not defined in `specify_params` will cause an error
- Refactor INI and priority handling to enable `specify_params`

### Other
- Strict substitution for environment variable templates; consistent with HOWTO on wiki

## v0.4.12: 2023-07-19

### Changed
- GCGI-956: The TMB plot has been moved to a linear format and the PGA plot has been removed

### Added
- GCGI-957: The number of candidate SNVs for the pWGS assay are listed in Genomic Landscape section

## v1.0.0-dev0.0.5: 2023-07-04

### GCGI-946: Versioning for plugins
- All plugins must output a "version" string in the JSON
- Updated `plugin_schema.json`, demo plugins, and tests

### GCGI-875: Simplify configurable interface
- Initialize components with a single `**kwargs` variable, for ease of calling superclass
- New `config_wrapper` class, with methods to read/edit the INI
- Reorganize core config classes into a single `configure.py` file

## v0.4.11: 2023-06-27

### Changed
- GCGI-864: removed annotation of 5'UTR, 3'UTR, and 3'Flank. 5'Flank only annotated if TERT
- Sample QC results moved to below summary
- Split some `Case Overview` section into a new `Patient and Physician` section
- Removed tracking of patient's genetic sex
- GCGI-943: Overrode HGVSp for BRAF V640E to be represented as V600E
- GCGI-942: Changed expected maf file extension from '.filter.deduped.realigned.recalibrated.mutect2.filtered.maf.gz' to '.mutect2.filtered.maf.gz'

## v0.4.10: 2023-06-06

### Changed
- ACD -> ACDx
- Added "-" between date and report name in footer
- GCGI-806: Modify `benchmark.py` interface; remove `--compare-all` option; add `--delta` argument for permitted difference in expression levels

### Fixed
- GCGI-870: Fix for biomarker annotation cache; required for benchmark cron

## v0.4.9: 2023-05-15

### Changed
- GCGI-883: Added date to footer of pdf, as in ISO requirement
- GCGI-865: replaced MSI LLOD text
- GCGI-885: Changed "Small regions (&#60;3 Mb) with large copy number gains" to "Regions with large copy number gains (&#8805; 6 CN)"
### Fixed
- GCGI-885: Fixed splice site reporting

## v0.4.8: 2023-04-25

### Changed
- updated version of Arriba from 1.2.0 to 2.4.0
- updated version of STAR from 2.7.3a to 2.7.10b
- updated pipeline version to 3.0

### Fixed
- GCGI-862: fixed fusion oncokb levels (changed to symbols)
- GCGI-853: fixed and cleaned annotation of genomic biomarkers
- GCGI-852: Correct file metatype for Mavis summary files

## v1.0.0-dev0.0.4: 2023-05-04

### GCGI-850: Priority order for components
- Control the order of configure/extract/render steps for all components
- A "component" is shorthand for a plugin, helper, or merger
- Introduce _priority_; steps are run from lowest to highest priority number
- Priority allows us to manage dependencies between components
- At configure (but not extract or render), the core has a priority which can be modified
- Parameters in INI and JSON for configure/render/extract priority

### Change to API

Configure and extract methods for a component take the entire ConfigParser object, not a section. This allows access to the config parameters of other components; as well as methods of ConfigParser, such as `set` and `getint`. While a component can _read_ any INI section during the configure step, it can only _write_ to its own named section of the INI.

### GCGI-837: Toolbox for configuration in `configurable.py`

Methods inherited by all components:
- Required/default parameters and parameter validation
- Get special directory paths from environment variables
- Handle component priorities
- Get/set/query INI params (other than priority levels)

## v1.0.0-dev0.0.3: 2023-04-19

- Bugfix for generating default JSON path in `core/main.py`

## v1.0.0-dev0.0.2: 2023-04-19

- GCGI-826: Update the main `djerba.py` script to run core/plugins, with tests. New `report` mode replaces `all` and `draft`. Supported modes: `configure`, `extract`, `html`, `report`. Other modes are TODO.
- GCGI-827: Workspace class with tests. Represents a shared directory to read/write files, similar to the "report" directory in classic Djerba.
- GCGI-838: Introducing "helper" modules, with an example which copies a subset of file provenance to the workspace.
- GCGI-839: Methods to read/write core config in the workspace, so it can be used by plugins

## v0.4.7: 2023-04-13

### Added
- GCGI-823: New script `src/test/run_gsicapbench.sh` to generate and compare benchmark reports before a release

### Fixed
- GCGI-810: Do not exit prematurely when finding benchmark inputs

## v1.0.0-dev0.0.1: 2023-04-11

- Pre-release for development of v1.1.0
- This will be the first of several pre-releases to track core/plugin development
- Git branch for pre-releases will be `GCGI-806_v1.0.0-dev`, not `master` GCGI-806_v1.0.0-dev

### Added

- Working prototypes of core/plugin functionality and testing

## v0.4.6: 2023-04-06

- With this release, we start a _feature freeze_ on the current Djerba application
- Urgent bugfixes only, to allow us to focus on implementing Djerba v1.0.0

### Added
- new parameter called `cbio_study_id` from shesmu for whizbam links

### Changed
- Moved qc-etl and pinery metric pulls to `discover_secondary` so that `tumour_id` is set first
- Check for manually configured parameters before querying qc-etl or Pinery
- Removed callability and coverage from `config_template.ini`
- Warning message about MSI LLOD in report when purity less than 50%

### Fixed
- Raise an error in INI config validation if any parameters are set to an empty string
- Removed unloading of djerba module in `qc_report` because both now use same python version
- More specific error messages when qc-etl and pinery pulls fail

## v0.4.5: 2023-03-24

### Fixed
- Add dependencies to `setup.py`, to resolve build error in Modulator

## v0.4.4: 2023-03-22

### Changed
- `djerba pdf` takes in dir/ and json and makes pdfs from htmls based on report_id in json ()
- Proteins for splice sites changed to form p? (c.${POSITION}${MUTATION}) (ex. from "p.X2540_splice" to "p.? (c.458-1G>T)")
- Updated to support mavis data given as .tab input (still supports .zip input)
- Updated to prevent error when mavis .tab file is empty or only contains a header
- target coverage pulled from pinery
- callability and coverage pulled from qc-etl
- automatically make failed report if coverage below target
- add `jsonschema` dependency in `setup.py`; not yet needed for production, but will be for plugin development
- move to python 3.10.6

## v0.4.3: 2023-03-10

### Changed
- Updated to use Python Tools module v17 for Geneticist Review Report

### Fixed
- GCGI-777: Stop `config.ini` validation from logging incorrect warnings
- GCGI-773: New limits to y-axis in CNV plot

## v0.4.2: 2023-03-07

### Fixed
- Add `research_report_template.html` to installation in `setup.py`

## v0.4.1: 2023-03-06

### Added
- GCGI-686: Simple demo of a plugin structure in `prototypes`
- GCGI-388: Versions for softwares and links are configurable

### Fixed
- GCGI-767: FPR check on sample type was too strict

## v0.4.0: 2023-03-01

- Requires update to `djerba_test_data_lfs`

### Added
- Automatically generates research report from template
- merges research and clinical reports
- new merger function
- MSI in clinical report

### Fixed
- Handle cases where expression percentile for a gene is not available

## v0.3.21: 2023-02-21

- Requires update to `djerba_test_data_lfs`

### Added
- GCGI-456: Add mRNA expression
- N1/N2/N3 icons for Oncogenic/Likely Oncogenic/Predicted Oncogenic

### Changed
- GCGI-663: Center OncoKB icons in table column
- GCGI-676: Use OncoKB icons in mutation sections
- GCGI-722: Fix page breaks
- GCGI-723: Extra line breaks in report footer

### Fixed
- GCGI-733: Bugfix for archiving crash on failed reports

## v0.3.20: 2023-01-27

### Added
- GCGI-587: Added CLIA number
- GCGI-652: Added description of Copy State changes in supplementary

### Fixed
- GCGI-698: Handle unknown cytoband without a misleading warning
- GCGI-702: Add apply/update cache options to benchmark script
- GCGI-703: Fix genome reference name in footer
- GCGI-675: Update default config ini parameters
- GCGI-692: Updated the Genomic Summary template

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
