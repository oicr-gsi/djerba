# OncoKB caching in Djerba

## Introduction

Djerba annotates its output using scripts from [oncokb-annotator](https://github.com/oncokb/oncokb-annotator). It also has the ability to cache the annotations offline in JSON format.

Caching of OncoKB annotation has the following advantages:
- Speed: The cache can be read in less than a second, whereas annotating a typical MAF file via OncoKB takes roughly 10 minutes
- Automated tests can be run without accessing the internet
- Reduces demands on the OncoKB server, especially during intensive testing

## Location and format

The cache is read from and/or written to a directory specified in the `oncokb_cache` field of the `[settings]` section in the Djerba INI file. A default cache location is configured with other default settings in [defaults.ini](../src/lib/djerba/data/defaults.ini). Cache files are written to a subdirectory named for the OncoTree code, eg. `paad` for pancreatic adenocarcinoma. Note that the `oncokb-annotator` scripts take the OncoTree code as input, and annotation may differ between OncoTree codes.

The cache for a given OncoTree code contains three JSON files, one each for CNA, fusion and MAF annotations. Each file contains a dictionary of annotations, whose keys are identifiers for the un-annotated input lines.

## Cache operations

Caching is all-or-nothing: Either Djerba gets all its annotations from the cache, or all from OncoKB. It is relevant for the `extract`, `draft`, and `all` modes of `djerba.py`.

There are two basic caching operations:
- Update: Generate a clinical report with annotations from OncoKB, and use the annotations to update the cache.
- Apply: Generate a clinical report with annotations from the cache, instead of from OncoKB.

These are activated respectively by the `--update-cache` and `--apply-cache` options on the command line. Attempting to use both options at once will raise an error.

If Djerba is run in WGS-only mode, no action will be taken on the fusion cache.

### Update

In update-cache mode, Djerba will:
- Download annotations for the given inputs from OncoKB
- Read the JSON cache files
- Update the files with the new JSON annotations.

Any annotations which have changed since the last cache update are overwritten with the new values. The updated JSON is then written to the cache directory.

### Apply

In apply-cache mode, Djerba will:
- Read annotations from the given cache directory
- Use the cached values to write output and generate a clinical report
- For CNA inputs, all reported variants must have annotations in the cache; for MAF and fusion, variants not found in the cache will receive default annotations. This is consistent with previously-existing Djerba practice of writing all variants for fusion and MAF, but only variants with annotation for CNA.

## Usage

### Automatic

A number of automated Djerba tests use the OncoKB cache to run more quickly and without accessing the internet. These include unit tests in `test.py` and automated testing against the `GSICAPBENCH` dataset. Caches for automatic usage will be backed up and/or under version control.

### Manual

If a clinical report is being generated multiple times, such as for tests or troubleshooting, waiting for annotation can be quite time-consuming. In this case, `djerba.py` can be used with `--update-cache` on an initial run, to populate the cache; and on subsequent runs with `--apply-cache`. The default cache for manual usage is _not_ backed up or controlled in any way, and should be considered a scratch space only.

The script `update_oncokb_cache.py` will update the cache files for given input and output directories. It is _not_ aware of the oncotree code, and should be given the full path to the cache directory.