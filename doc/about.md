(about)=

# Introduction

## What is Djerba?

[Djerba](https://github.com/oicr-gsi/djerba) is a system for generating [clinical report documents](https://github.com/oicr-gsi/djerba/blob/main/examples/WGTS/PLACEHOLDER-v1_report.clinical.pdf) from pipeline data, with a modular structure based on plugins. It is named after a [Mediterranean island](https://en.wikipedia.org/wiki/Djerba) and pronounced "jerba" (the initial letter D is silent).

## What Does Djerba Do?

Djerba inputs a config file and outputs a report.

The config file is in the widely-used [INI format](https://docs.python.org/3/library/configparser.html).

The report contains equivalent information in three different formats: JSON, HTML, and PDF.
- JSON is a machine-readable format for the report data.
- HTML is used for typesetting, to specify the report appearance.
- PDF is shared with clinical practicioners.

## How To Use This Documentation

The [How Djerba Works](how_djerba_works) section briefly covers key concepts and terminology. We recommend it as a starting point for all Djerba users.

The [User Guide](user_guide) describes how to install Djerba, and run existing plugins to produce reports.

The [Component Reference](component_reference) has detailed descriptions of plugins and other components of Djerba, used for clinical reporting at OICR.

We encourage users to write their own plugins, as described in the [Developer Guide](developer_guide).

Finally, the [Contact](contact) section has contact links for the Djerba developers, and some brief notes on development policy.

## Copyright and Licensing

Copyright &copy; 2020-2026 by Genome Sequence Informatics, [Ontario Institute for Cancer Research](https://oicr.on.ca/). All rights reserved.

Licensed under the [GPL 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).
