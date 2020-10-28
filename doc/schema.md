# Djerba JSON schema

Djerba validates input config files against a [JSON schema document](../src/lib/djerba/data/input_schema.json), in the format defined by [json-schema.org](https://json-schema.org).

Validation is automatically run by the command-line script [djerba.py](../src/bin/djerba.py) in `elba` or `cbioportal` modes; and can be run as a standalone operation by using `validate` mode.

The JSON schema is used to check the syntax of the config file. Additional validation beyond the scope of the JSON schema is done by Djerba, eg. checking if output locations are writable.

Notable features of the schema are described below, using JSON terminology. So an "array" is a list of items; and an "object" is a structure of key/value pairs, corresponding to a Python dictionary.

## Schema root

### Required entries

Minimal configuration for writing Elba config JSON.

- `samples`: Array of objects. Each object in the array must have a `SAMPLE_ID` key.
- `genetic alterations`: Array of objects. Each object in the array represents a type of input data; see below for details of the required schema.

### Optional entries

Additional configuration for writing a cBioPortal report directory. These entries are optional; but if any one of them is present, they must all be present. Each entry has requirements for internal structure; see the [JSON schema document](../src/lib/djerba/data/input_schema.json) for details.

- `case_lists`
- `cancer_type`
- `samples_meta`
- `study_meta`

## Genetic alteration schema

The JSON objects in the `genetic_alterations` array are used to construct instances of the [genetic_alteration](../src/lib/djerba/genetic_alteration.py) Python class, which in turn process the input data.

### Required entries

- `datatype`: String. Based on the [cBioPortal](https://docs.cbioportal.org/5.1-data-loading/data-loading/file-formats) datatype, eg. MAF or FUSION. May also take the special value MULTIPLE; this allows a single `genetic_alteration` to encompass multiple cBioPortal datatypes, for example CONTINUOUS and Z-SCORE for expression data.
- `genetic_alteration_type`: String. Based on the parameter of the same name in cBioPortal metadata. Djerba defines some additional types not present in cBioPortal, such as CUSTOM_ANNOTATION.
- `input_directory`: String. Path to the directory containing input files.
- `input_files`: Object; may be empty. Keys are sample identifiers, corresponding to the SAMPLE_ID field in the `samples` entry; values are filenames.
- `metadata`: Object. Contains any additional parameters required by the genetic alteration. The exact contents will vary by genetic alteration type.

### Optional entries

- `workflow_run_id`: An identifier for the workflow run which produced the genetic alteration data.
