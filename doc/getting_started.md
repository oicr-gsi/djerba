(getting_started)=

# Getting started

## Welcome to Djerba!

Djerba was developed by and for the CGI team at [OICR](https://oicr.on.ca/); but its modular plugin structure is intended to enable external collaboration.

In other words: You are welcome to write your own plugins!

The first step is to run [djerba-demo](https://github.com/oicr-gsi/djerba-demo). This is a fork of production Djerba, with [complete instructions](https://github.com/oicr-gsi/djerba-demo/blob/main/HOWTO.md) for installation, testing, and generating example reports. It also includes a [Frequently Asked Questions](https://github.com/oicr-gsi/djerba-demo/blob/main/FAQ.md) page.

## Next Steps

Once you have successfully run [djerba-demo](https://github.com/oicr-gsi/djerba-demo), you are ready to try writing your own plugins.

The [djerba-demo](https://github.com/oicr-gsi/djerba-demo) repo contains a fully functional version of the Djerba core code (version 1.6.4), but with a reduced set of plugins. If you wish to write your own plugins, we recommend forking [djerba-demo](https://github.com/oicr-gsi/djerba-demo) and creating packages in the [plugins directory](https://github.com/oicr-gsi/djerba-demo/tree/main/src/lib/djerba/plugins). The [Plugin Developer's Guide](plugin_developers_guide) provides further instructions and tips.

## Production Djerba

The [production Djerba code](https://github.com/oicr-gsi/djerba) has a number of internal OICR dependencies. Deployment by external users is not currently supported. However, we have plans to reorganize the code and make production Djerba available externally by the end of 2024.

## Questions and Troubleshooting

Support for external development is a work in progress. Known issues are listed on [Github](https://github.com/oicr-gsi/djerba/issues); feel free to [contact](contact) the Djerba developers with any additional questions or concerns.

