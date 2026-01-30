(user_guide)=

# User Guide

In this section, we describe how to install Djerba and run it to produce reports.

## Installing Djerba

### Requirements

#### Hardware

- The core Djerba functions are very lightweight, 4 GB of RAM and a 1 GHz processor should be more than sufficient to run them.
- Certain plugins are more demanding, and may need up to 16GB of RAM and a 4 GHz or faster processor (preferably with multiple cores).
- A full installation of Djerba and its mainline plugins requires about 600 MB of disk space.

#### Operating System

- Djerba runs in production under Ubuntu 22.04 LTS.
- Other versions of Linux should work with no difficulty.
- Limited testing of Djerba has successfully been carried out on MacOS.
- Djerba has _not_ been tested on Windows, and issues are likely to occur.

#### Software

- [Python](https://www.python.org/downloads/) version 3.10 or greater (at time of writing, if in doubt consult the [setup script](https://github.com/oicr-gsi/djerba/blob/main/setup.py))
- The [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html) binary must be on the system `PATH`.
- For best results, the Arial font family should be installed (in `$HOME/.local/share/fonts` on a Linux machine).
- Plugins may have additional dependencies; consult the documentation for the individual plugin.

### How To Install

The core functions of Djerba are written in Python, and Djerba is installed using standard Python tools.

If you are unfamiliar with installing Python programs, we recommend consulting the [official Python documentation](https://docs.python.org/3/), in particular the [Python Packaging User Guide](https://packaging.python.org/en/latest/). You may wish to use a [Python virtual environment](https://docs.python.org/3/library/venv.html) to install Djerba without affecting your system Python directories.

From a download or clone of the Djerba repository, simply run `pip3 install .`. This will install Djerba and all its Python dependencies.

Djerba has a [setup.py script](https://github.com/oicr-gsi/djerba/blob/main/setup.py) which specifies exactly what is installed.

Note that Djerba plugins may contain R scripts and other non-Python code. Installing with `pip3` _will_ copy these files to the installation directory, but _will not_ install non-Python dependencies such as R libraries. Any such dependencies must be installed separately by the user. Consult documentation for individual plugins for details.

## Running Djerba

### Environment Variables

Djerba uses a number of [environment variables](https://help.ubuntu.com/community/EnvironmentVariables) to configure its behaviour.

| Variable | Type | Description |
| :---- | :---- | :---- |
| `DJERBA_ARCHIVE_CONFIG` | INI file | Upload of JSON report documents to a [CouchDB database](FIXME_link) |
| `DJERBA_BASE_DIR`       | Directory | Base directory where Djerba was installed |
| `DJERBA_CORE_HTML_DIR`  | Directory  | Location of templates and stylesheets for core HTML rendering  |
| `DJERBA_RUN_DIR`        | Directory  | Location of the `util/data` subdirectory of the Djerba installation |
| `DJERBA_PACKAGES`       | Colon-separated list | Names of top-level Djerba packages; see [external plugins](FIXME)  |
| `DJERBA_PRIVATE_DIR`    | Directory  | Location of "private" files. |
| `DJERBA_TEST_DIR`       | Directory  | Location of data for unit tests  |
| `DJERBA_TEST_DATA`      | Directory  | Synonym for `DJERBA_TEST_DIR`. Deprecated, but still used by some plugins. | 

#### Required and Optional Variables

The `DJERBA_BASE_DIR`, `DJERBA_RUN_DIR`, and `DJERBA_PRIVATE_DIR` variables must be correctly set at runtime.

`DJERBA_ARCHIVE_CONFIG` is required unless the `--no-archive` command-line option is in effect.

If `DJERBA_CORE_HTML_DIR` is not set, it defaults to an appropriate directory in the Djerba installation.

If `DJERBA_PACKAGES` is not set, it defaults to the Djerba installation directory.

`DJERBA_TEST_DIR` and `DJERBA_TEST_DATA` are needed for testing only, not production.

#### The `DJERBA_PRIVATE_DIR`

This is a catch-all location where Djerba can read and write reference files.

It contains the [username config file](FIXME).

It is also the output location for the [activity tracker](FIXME). If the tracker is in use, `DJERBA_PRIVATE_DIR` must have a subdirectory called `tracking`.

### Core Configuration Files

Some core functions of Djerba are controlled using configuration files. These are distinct from the INI configuration file used to run Djerba and generate a report.

#### Archive Config

The INI file specified by `DJERBA_ARCHIVE_CONFIG` controls upload of JSON report documents to the Djerba [CouchDB database](FIXME).

Note that archiving is optional, and may be omitted with the `--no-archive` option to the `djerba.py` script.

##### Example

```
[archive]
database_name = djerba
username = djerba_production_user
password = VerySecretPassword
address = my-djerba-server.example.com
port = 1234
```

#### User Name Config

JSON file to map from UNIX username to a display name for report documents. Djerba reads this configuration from the `djerba_users.json` file in the directory specified by the `DJERBA_PRIVATE_DIR` environment variable.

Djerba looks up the username using standard UNIX environment variables: It first tries `USER`; if there is no config entry, it next tries `SUDO_USER`; then it falls back to using UNIX username as the display name.

##### Example

```
{
    "jlpicard": "Jean-Luc Picard",
    "bcrusher": "Beverly Crusher"
}
```

#### HTML Configuration Files

Djerba uses templates and stylesheets to control the overall look-and-feel of the HTML report output.

The default versions of these files have the OICR branding and colour scheme. They are part of the Djerba [source code](https://github.com/oicr-gsi/djerba/tree/main/src/lib/djerba/core/html) and are copied to the Djerba installation directory. The user may set an alternate location for these files using the `DJERBA_CORE_HTML_DIR` environment variable.

### Configuring the INI File

TODO Example goes here

### The `djerba.py` Script

The main command-line interface for Djerba is the `djerba.py` script.

TODO Example goes here

### Other Command-Line Scripts

Other command-line scripts installed with Djerba include:

- [generate_ini.py](https://github.com/oicr-gsi/djerba/blob/main/src/bin/generate_ini.py): Generate a "blank" INI file for a named list of Djerba components. For regular use, this has been superseded by the `setup` mode of `djerba.py`. Retained for use by plugin developers.
- [mini_djerba.py](https://github.com/oicr-gsi/djerba/blob/main/src/bin/mini_djerba.py): Simplified script to update patient info and summary text in a Djerba report. Currently not supported, may be revived at a future date.
- [update_oncokb_cache.py](https://github.com/oicr-gsi/djerba/blob/main/src/bin/update_oncokb_cache.py): Update an offline cache of variant annotation, used for testing.
- [validate_plugin_json.py](https://github.com/oicr-gsi/djerba/blob/main/src/bin/validate_plugin_json.py): Check if plugin output is valid according to the Djerba JSON schema. Intended for plugin developers.

Run any script with `-h/--help` for details.
