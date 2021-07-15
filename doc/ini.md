# Djerba INI file structure

## Introduction

Djerba uses the [INI file format](https://en.wikipedia.org/wiki/INI_file) for input configuration, as implemented in the Python [configparser](https://docs.python.org/3/library/configparser.html) module.

The main Djerba script will exit with an error if required parameters are missing. It will log a warning if additional, unknown config parameters are found.

### Reminder: Djerba steps

Djerba works in 4 steps:
1. `configure`: Input user configuration and populate optional values
2. `extract`: Find metric values from the inputs specified in configuration
3. `html`: Take output from the `extract` step and write an HTML report
4. `pdf`: Convert the HTML report to PDF

The main Djerba script also has an `all` mode, which runs all four steps in sequence.

### Optional and required parameters

Djerba has two types of INI parameter:
- **Required:** These cannot be found automatically by Djerba, and must be specified in the INI file input to `configure`. Sources of required parameters include the requisition system and Dashi. (Some required parameters may become optional in future releases of Djerba, as more automation is added.)
- **Optional:** These may be added to the INI file input to the `configure` step, but are not compulsory. If an optional parameter is specified in INI input to the `configure` step, then `configure` will not overwrite it.

It follows that Djerba INI files come in two different types:
- **Partially-specified**: An INI file with some parameters specified. This is input to `configure`, which automatically fills in missing values and outputs a fully-specified INI file. Example: [config_user.ini](../src/test/data/config_user.ini)
- **Fully-specified**: An INI file with all parameters specified. This is output from the `configure` step, and input to `extract`. Example: [config_full.ini](../src/test/data/config_full.ini)

## INI sections

The INI file is divided into a number of sections, with headers in square brackets.

| Name         | Optional/Required  | Description                              |
|--------------|--------------------|------------------------------------------|
| `[inputs]`   | Required | Required parameters from the user                  |
| `[settings]` | Optional | Parameters relating to the installation and operation of Djerba itself. Not expected to change often. |
| `[seg]`      | Optional | Thresholds for copy number alteration calculations on .seg files. If not given, they take default values.   |
| `[discovered]` | Optional | Parameters automatically discovered by Djerba, by reading file provenance, parsing workflow outputs, etc. |

## INI parameters

### Required parameters

All required parameters go in the `[inputs]` section. The "Source" column lists data source, as per version 2.0 of SOP "TM-005: Data Review and Reporting Procedure"; where "req" denotes the requisition system, and "user" denotes the member of CGI staff compiling the report.

| Name                   | Source | Notes                                                    |
|------------------------|----------|------------------------------------------------|
| `mean_coverage`            | Dashi | |
| `oncotree_code`             | req       | [OncoTree](http://oncotree.mskcc.org/#/home) code (case-insensitive), eg. paad |
| `patient`                | req       | Study name and patient number, eg. PANX_1249 |
| `pct_v7_above_80x`            | Dashi | |
| `report_version`            | user | |
| `sample_anatomical_site`            | req | |
| `sample_type`            | req | |
| `sex`            | req | Patient sex |
| `studyid`                | req       | Study ID within requisition system, eg. PASS01 |
| `tcgacode`                | req    | [TCGA](https://www.cancer.gov/about-nci/organization/ccg/research/structural-genomics/tcga) code for the tumour, eg. PAAD |

### Optional parameters

#### Parameter sources

Sources of optional parameters include:
- INI file with constants: [defaults.ini](../src/lib/djerba/data/defaults.ini)
- Path relative to the Djerba installation directory
- Discovery from file provenance
- Computing a heuristic to find a default value, for Sequenza gamma

#### Configuring `data_dir` parameters

The automatic parameter discovery first finds the `data_dir` parameter, relative to the Djerba installation path; it then finds other paths relative to `data_dir`, as listed in the table below. If `data_dir` is specified in user config, those parameters will be found relative to the manually-specified path, not the automatic one. This can be used to specify different reference files if needed. For finer control, any individual `data_dir` parameter can be overridden in user config, while leaving the others unaffected.

In particular, the `genomic_summary` parameter can be used to specify a manually-written text file instead of the default placeholder.

So, there are three different ways to configure a `data_dir` parameter such as `genomic_summary`:
1. Default: Djerba finds the default `data_dir`, which contains a default `genomic_summary` file.
2. Alternative directory: If `data_dir` is specified in user config, Djerba will look in that directory for a `genomic_summary` file.
3. Alternative file: If `genomic_summary` is specified in user config, Djerba will use that file, regardless of the value of `data_dir`.

#### Table of optional parameters

| Section        | Name          | Source | Notes                                          |
|----------------|---------------|-------------| -----------------------------------|
| `[discovered]` | `data_dir`    | Djerba installation | Directory for miscellaneous data files          |
| `[discovered]` | `enscon`    | `data_dir` | Ensembl conversion file                    |
| `[discovered]` | `entcon`    | `data_dir` | Entrez conversion file                    |
| `[discovered]` | `gamma`     | Default computation       | Sequenza gamma parameter  |
| `[discovered]` | `genebed`    | `data_dir` | Interval file                    |
| `[discovered]` | `genelist`    | `data_dir` | Gene list file                   |
| `[discovered]` | `genomic_summary`    | `data_dir` | Genomic summary file                   |
| `[discovered]` | `gep_file`    | File provenance | GEP input file from RSEM                    |
| `[discovered]` | `maf_file`    | File provenance | MAF input file from VariantEffectPredictor                 |
| `[discovered]` | `mavis_file`  | File provenance | Mavis input file                                 |
| `[discovered]` | `mutation_nonsyn`    | `data_dir` | Non-synonymous mutation list file                    |
| `[discovered]` | `normal_id` | File provenance | Normal ID, eg. 100-PM-013_BC                |
| `[discovered]` | `oncolist`    | `data_dir` | OncoKB listing file                    |
| `[discovered]` | `oncotree_data`    | `data_dir` | [OncoTree](http://oncotree.mskcc.org/#/home) data file with cancer type and description                    |
| `[discovered]` | `patient_id` | File provenance | Patient ID, eg. 100-PM-013                                 |
| `[discovered]` | `sequenza_file` | File provenance |Sequenza input file                                 |
| `[discovered]` | `tmbcomp` | `data_dir` | TCGA TMB file                                 |
| `[discovered]` | `tumour_id` | File provenance | Tumour ID, eg. 100-PM-013_LCM5                |
| `[seg]`        | `ampl` | defaults.ini |  |
| `[seg]`        | `gain` | defaults.ini |  |
| `[seg]`        | `hmzd` | defaults.ini |  |
| `[seg]`        | `htzd` | defaults.ini |  |
| `[settings]`   | `bed_path` | defaults.ini |  |
| `[settings]`   | `gep_reference` | defaults.ini |  |
| `[settings]`   | `min_fusion_reads` | defaults.ini |  |
| `[settings]`   | `provenance` | defaults.ini | Path to file provenance report  |
| `[settings]`   | `tcga_data` | defaults.ini | Path to TCGA data directory  |
| `[settings]`   | `whizbam_url` | defaults.ini | Base URL of OICR Whizbam site; used to construct links in report  |

## Summary

- Required parameters *must* be supplied by the user in the `[inputs]` section of the INI file.
- Optional parameters *may* be suppllied by the user, in other sections of the INI file. If so, they will be used in preference to values generated by Djerba.
