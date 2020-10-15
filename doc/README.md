Djerba documentation
====================

The `doc` directory contains additional documentation and examples.

## HTML documentation

[HTML documentation](./doc/html/djerba/index.html) pages were generated using [pdoc3](https://pdoc3.github.io/pdoc/). These incorporate documentation strings from source code, and show the structure of classes and methods.

## Elba config output

Two examples of Elba config output:
- **Old version**: [elba_config.json](./elba_config.json) is a JSON spec for the Elba report configuration. It was presented at the [2020-09-15 CGI meeting](https://wiki.oicr.on.ca/pages/viewpage.action?spaceKey=GSI&title=2020-09-15+CGI+Meeting). It is kept here for now, for historical/discussion interest.
- **New version**: [elba_expected_mx.json](../src/test/data/elba_expected_mx.json) is expected test output from Djerba has been modified slightly from the above format.

As of 2020-10-08, initial development of Elba and Djerba is ongoing, and the Elba config structure is not yet finalised.

TODO: Supplement the example JSON files with a formal [JSON schema](https://json-schema.org/).
