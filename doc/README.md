Djerba documentation
====================

The `doc` directory contains additional documentation and examples.

## HTML documentation

[HTML documentation](./html/djerba/index.html) pages were generated using [pdoc3](https://pdoc3.github.io/pdoc/). These incorporate documentation strings from source code, and show the structure of classes and methods.

## Input JSON schema

Described in [schema.md](./schema.md).

## MAF input format

MAF file format used for `MUTATION_EXTENDED` metrics is described in [maf.md](./maf.md).

## Elba config output

- [elba_config_example.json](./elba_config_example.json) is an example of Elba report configuration JSON. A schema for Elba config output is in the [elba-config-schema](https://github.com/oicr-gsi/elba-config-schema) repository. Djerba output is validated against the Elba config schema; see the unit tests for details.

