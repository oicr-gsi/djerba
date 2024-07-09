# djerba-demo: Frequently Asked Questions

### Can I fork and modify the Djerba software?

Yes -- Djerba is licensed under [GPL 3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) and may be shared and changed accordingly.

### Who is the copyright holder for Djerba?

Djerba is copyright &copy; Genome Systems Informatics, Ontario Institute for Cancer Research; all rights reserved.

### Can I write my own Djerba plugins?

Yes! We have a [Plugin Developer's Guide](https://djerba.readthedocs.io/en/latest/plugin_howto.html) on ReadTheDocs.

### How do I remove the OICR logo and letterhead from the top of the report?

The simplest way of doing so is to give your plugins the attribute `simple`, instead of `clinical` as in the demonstration plugins.

### How can I contact the Djerba developers?

Raise an issue on the [Github page](https://github.com/oicr-gsi/djerba-demo/issues).

### What is "alternate_djerba"?

Djerba supports importing plugin code from namespaces other than the main `djerba` package. The [alternate_djerba](https://github.com/oicr-gsi/djerba-demo/tree/main/src/lib/alternate_djerba) directory is used to test this functionality.

### This file/script/module looks interesting, what does it do?

The `djerba-demo` repository is a fork of production Djerba. In addition to the demonstration plugins, some production code has been left in place for testing purposes or simply to save time. If you have specific questions about the code, we recommend looking at the [main Djerba repo](https://github.com/oicr-gsi/djerba) in the first instance, to see how it works in production.

### Djerba isn't working for me; what should I do?

If you have any issues, contact the developers and we will do our best to help.

Please note that Djerba was developed to generate clinical reports for cancer patients at the Ontario Institute for Cancer Research. Fixes and improvements to clinical report production have the highest priority for developer time. We appreciate your understanding.
