# Djerba INI file structure

## Introduction

Djerba uses the [INI file format](https://en.wikipedia.org/wiki/INI_file) for input configuration, as implemented in the Python [configparser](https://docs.python.org/3/library/configparser.html) module.

The main Djerba script will exit with an error if required parameters are missing. It will log a warning if additional, unknown config parameters are found.

### Reminder: Djerba steps

Djerba works in 4 main steps:
1. `configure`: Input user configuration and populate optional values
2. `extract`: Find metric values from the inputs specified in configuration
3. `html`: Take output from the `extract` step and write an HTML report
4. `pdf`: Convert the HTML report to PDF

The `configure` step populates the INI; while the `extract` step applies parameters in the INI, and writes intermediate results to a reporting directory. An INI file is not used in the `html` and `pdf` steps.

### Optional and required parameters

Djerba has two types of INI parameter:
- **Required:** These cannot be found automatically by Djerba, and must be specified in the INI file input to `configure`. Sources of required parameters include the requisition system and Dashi. (Some required parameters may become optional in future releases of Djerba, as more automation is added.)
- **Optional:** These may be added to the INI file input to the `configure` step, but are not compulsory. If an optional parameter is specified in INI input to the `configure` step, then `configure` will not overwrite it.

It follows that Djerba INI files come in two different types:
- **Partially-specified**: An INI file with some parameters specified. This is input to `configure`, which automatically fills in missing values and outputs a fully-specified INI file. Example: [config_user.ini](../src/test/data/config_user.ini)
- **Fully-specified**: An INI file with all parameters specified. This is output from the `configure` step, and input to `extract`. Example: [config_full.ini](../src/test/data/config_full.ini)

## INI sections

The INI file is divided into sections, with headers in square brackets.

| Name         | Optional/Required  | Description                              |
|--------------|--------------------|------------------------------------------|
| `[inputs]`   | Required | Required parameters from the user                  |
| `[settings]` | Optional | Parameters relating to the installation and operation of Djerba itself. Not expected to change often. |
| `[discovered]` | Optional | Parameters automatically discovered by Djerba, by reading file provenance, parsing workflow outputs, etc. |

## Required INI parameters

All required parameters go in the `[inputs]` section. The "Source" column lists data source, as per SOP "TM-005: Data Review and Reporting Procedure"; where "req" denotes the requisition system, and "user" is the member of CGI staff compiling the report.

| Name                   | Source | Notes                                                    |
|------------------------|----------|------------------------------------------------|
| `mean_coverage`            | Dashi | |
| `oncotree_code`             | req       | [OncoTree](http://oncotree.mskcc.org/#/home) code (case-insensitive), eg. paad |
| `patient`                | req       | Study name and patient number, eg. PANX_1249; aka _root sample name_ |
| `requisition_id`                | req       | Requisition id, eg. PASS01-UHN-001; |
| `projectid`                | dimsum       | Project ID within Provenance, eg. PASS01 |
| `pct_v7_above_80x`            | Dashi | |
| `report_version`            | user | |
| `req_approved_date`            | req | Format must be `YYYY/MM/DD` |
| `sample_anatomical_site`            | req | |
| `sample_type`            | req | |
| `sequenza_reviewer_1` | user | Name of first reviewer for Sequenza parameters |
| `sequenza_reviewer_2` | user | Name of second reviewer for Sequenza parameters |
| `sex`            | req | Patient sex |
| `studyid`                | req       | Study ID to be displayed in report, eg. PASS-01 |
| `tcgacode`                | req    | [TCGA](https://www.cancer.gov/about-nci/organization/ccg/research/structural-genomics/tcga) code for the tumour, eg. PAAD |

## Optional INI parameters

### Sources

Sources of optional parameters include:
- INI file with constants: [defaults.ini](../src/lib/djerba/data/defaults.ini)
- Path relative to the Djerba installation directory
- Discovery from file provenance
- Computed from other parameters

### Resolution order

Some parameters depend on others for their default values. The order of parameter resolution reflects this.

#### `data_dir`

The `data_dir` parameter contains various data files used by Djerba; default files form part of the Djerba installation.

Automatic parameter discovery first finds `data_dir`, relative to the Djerba installation path; it then finds other paths relative to `data_dir`, as listed in the table below. If `data_dir` is specified in user config, those parameters will be found relative to the manually-specified path, not the automatic one. This can be used to specify different reference files if needed. For finer control, any individual `data_dir` parameter can be overridden in user config, while leaving the others unaffected.

So, there are three different ways to configure a `data_dir` parameter such as `oncolist`:
1. Default: Djerba finds the default `data_dir`, which contains a default `oncolist` file.
2. Alternative directory: If `data_dir` is specified in user config, Djerba will look in that directory for a `oncolist` file.
3. Alternative file: If `oncolist` is specified in user config, Djerba will use that file, regardless of the value of `data_dir`.

#### Sequenza and logR cutoffs

| Parameters                               | Dependency                                              |
|------------------------------------------|---------------------------------------------------------|
| `sequenza_gamma`, `sequenza_solution`    | `sequenza_file`                                         |
| `purity`, `ploidy`                       | `sequenza_file`, `sequenza_gamma`, `sequenza_solution`  |
| `ampl`, `gain`, `hmzd`, `htzd`           | `purity`                                                |

These parameters are resolved in dependency order:
1. Main group of parameters, including `sequenza_file`
2. `sequenza_gamma`, `sequenza_solution`
3. `purity`, `ploidy`
4. logR cutoffs: `ampl`, `gain`, `htzd`, `hmzd`

Permitted values for `sequenza_solution` are either "primary"; or the name of a Sequenza alternate solution directory, such as "sol2_0.28".

Recommended usage is:
- After reviewing the Sequenza results as per the SOP, manually configure `sequenza_gamma` and `sequenza_solution`
- Allow Djerba to automatically discover `purity` and `ploidy`, to ensure they are consistent with Sequenza gamma and solution
- logR cutoffs may be either manually configured or automatically discovered, as decided by the user

### Sample name parameters

Each donor has exactly one _root sample name_, which is supplied in the `patient` INI parameter and corresponds to one or more _sample names_.

A Djerba report uses:
- A whole genome normal (reference) sample
- A whole genome tumour sample
- Optionally, a whole transcriptome sample

Each sample is identified by a distinct _sample name_.

If Djerba is able to resolve the samples from file provenance without ambiguity, it will do so.

If not, for instance because multiple requisitions and samples correspond to the same patient, the sample names must be specified using the various `sample_name_*` parameters in the INI.

If _any_ sample name parameters are specified, then they must _at least_ include the whole genome tumor and normal names, and _optionally_ the whole transcriptome name.

### Table of optional parameters

| Section        | Name          | Source | Notes                                          |
|----------------|---------------|-------------| -----------------------------------|
| `[discovered]` | `ampl` | Computed from `purity` | logR cutoff value  |
| `[discovered]` | `data_dir`    | Djerba installation | Directory for miscellaneous data files          |
| `[discovered]` | `enscon`    | `data_dir` | Ensembl conversion file                    |
| `[discovered]` | `entcon`    | `data_dir` | Entrez conversion file                    |
| `[discovered]` | `gain` | Computed from `purity` | logR cutoff value |
| `[discovered]` | `genebed`    | `data_dir` | Interval file                    |
| `[discovered]` | `genelist`    | `data_dir` | Gene list file                   |
| `[discovered]` | `genomic_summary`    | `data_dir` | Genomic summary file                   |
| `[discovered]` | `technical_notes`    | `data_dir` | Technical notes file                   |
| `[discovered]` | `gepfile`    | File provenance | GEP input file from RSEM                    |
| `[discovered]` | `hmzd` | Computed from `purity` | logR cutoff value |
| `[discovered]` | `htzd` | Computed from `purity` | logR cutoff value |
| `[discovered]` | `maf_file`    | File provenance | MAF input file from VariantEffectPredictor       |
| `[discovered]` | `mavis_file`  | File provenance | Mavis input file                                 |
| `[discovered]` | `msi_file`  | File provenance | msisensor input file        
| `[discovered]` | `mutation_nonsyn`    | `data_dir` | Non-synonymous mutation list file             |
| `[discovered]` | `normalid` | File provenance | Normal ID, eg. 100-PM-013_BC                |
| `[discovered]` | `ploidy` | Read from `sequenza_file`, `sequenza_gamma`, `sequenza_solution` | Estimated tumour ploidy  |
| `[discovered]` | `purity` | Read from `sequenza_file`, `sequenza_gamma`, `sequenza_solution` | Estimated tumour purity  |
| `[discovered]` | `oncolist`    | `data_dir` | OncoKB listing file                    |
| `[discovered]` | `oncotree_data`    | `data_dir` | [OncoTree](http://oncotree.mskcc.org/#/home) data file with cancer type and description                    |
| `[discovered]` | `patientid` | File provenance | Patient ID, eg. 100-PM-013                                 |
| `[discovered]` | `sample_name_whole_genome_normal` | File provenance | Whole genome normal sample name, eg. PANX_1288_Ly_R_PE_567_WG |
| `[discovered]` | `sample_name_whole_genome_tumour` | File provenance | Whole genome tumour sample name, eg. PANX_1288_Pm_M_PE_558_WG |
| `[discovered]` | `sample_name_whole_transcriptome` | File provenance | Whole transcriptome sample name, eg. PANX_1288_Pm_M_PE_314_WT |
| `[discovered]` | `sequenza_file` | File provenance |Sequenza input file                                 |
| `[discovered]` | `sequenza_gamma`     | Default computation       | Sequenza gamma parameter  |
| `[discovered]` | `sequenza_solution`     | Default computation       | Sequenza solution identifier  |
| `[discovered]` | `tmbcomp` | `data_dir` | TCGA TMB file                                 |
| `[discovered]` | `tumour_id` | File provenance | Tumour ID, eg. 100-PM-013_LCM5                |
| `[settings]`   | `archive_name` | defaults.ini | name of archive on couchDB |
| `[settings]`   | `archive_url` | defaults.ini | url of archive on couchDB |
| `[settings]`   | `assay_version` | defaults.ini | Current version number of the WGTS assay |
| `[settings]`   | `bed_path` | defaults.ini |  |
| `[settings]`   | `gep_reference` | defaults.ini |  |
| `[settings]`   | `min_fusion_reads` | defaults.ini |  |
| `[settings]`   | `pipeline_version` | defaults.ini | Current version number of the WGTS pipeline |
| `[settings]`   | `provenance` | defaults.ini | Path to file provenance report  |
| `[settings]`   | `tcga_data` | defaults.ini | Path to TCGA data directory  |
| `[settings]`   | `whizbam_url` | defaults.ini | Base URL of OICR Whizbam site; used to construct links in report  |

### Sequenza metadata

These parameters are not directly used to generate the HTML report; instead, they store metadata values for later reference.

The following Sequenza parameters are written to a file `sequenza_meta.txt` in the reporting directory:
- `sequenza_file`
- `sequenza_gamma`
- `sequenza_reviewer_1`
- `sequenza_reviewer_2`
- `sequenza_solution`

