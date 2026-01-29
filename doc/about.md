(about)=

# Introduction

## What is Djerba?

[Djerba](https://github.com/oicr-gsi/djerba) is a system for generating [clinical report documents](https://github.com/oicr-gsi/djerba/blob/main/examples/WGTS/PLACEHOLDER-v1_report.clinical.pdf) from pipeline data, with a modular structure based on plugins. It is named after a [Mediterranean island](https://en.wikipedia.org/wiki/Djerba) and pronounced "jerba" (the initial letter D is silent).

## What does Djerba do?

Djerba inputs a config file and outputs a report.

The config file is in the widely-used INI format.

The report contains equivalent information in three different formats: JSON, HTML, and PDF.
- JSON is a machine-readable format for the report data.
- HTML is used for typesetting, to specify the report appearance.
- PDF is shared with clinical practicioners.

## Documentation

- [](how_djerba_works): Outline of basic concepts 
- [](user_guide): How to run Djerba and produce reports
- [](developer_guide): How to write Djerba plugins
- [](component_reference): Detailed reference for Djerba plugins and other components
- [](contact): Contact the Djerba developers

## Copyright and Licensing

Djerba was developed by the Clinical Genome Interpretation group, part of Genome Sequence Informatics at the [Ontario Institute for Cancer Research](https://oicr.on.ca/).

Copyright &copy; 2020-2026 by Genome Sequence Informatics, Ontario Institute for Cancer Research. All rights reserved.

Licensed under the [GPL 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).
