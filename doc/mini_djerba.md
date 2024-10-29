
# Mini-Djerba

## Introduction

Mini-Djerba allows a clinical geneticist to update personal health information (PHI) and edit the results summary in a Djerba report.

Input to mini-djerba is a file in [JSON format](https://en.wikipedia.org/wiki/JSON) containing clinical report data. Filenames are typically of the form `[report_id].json`, eg. `100-009-005_LCM3-v1_report.json`.

Steps are as follows:
1. Generate an initial PDF report for inspection
2. Generate config files
3. Edit the config files with PHI values and summary text
4. Use the config files to generate a new PDF with the updated PHI and summary

Mini-Djerba is distributed as a single, executable file. It is a command-line application; run with `-h` for help.

In brief, usage is `mini-djerba [global options] [mode] [options]`

Available modes are:
- `setup`: Generate INI and TXT config files, respectively with PHI and summary text, to be edited by the user
- `report`: Generate a PDF report from JSON input, with desired changes (if any)

## Usage

### Initial PDF without changes

We start by rendering the machine-readable JSON to human-readable PDF, without any changes.

Example:

```
mini-djerba render -j report.json
```

The default location for output is a PDF file in the current working directory named `[report_id].clinical.pdf`. We can write to a different directory with the `-o` option:

```
mini-djerba render -j report.json -o /my/output/directory
```

### Generate config files

Mini-Djerba accepts two config files:
- INI format, to update PHI
- TXT (plain text) format, to update summary text

The `setup` mode generates these files.
- If given a JSON file as input using the `-j` option, it will fill in values from the JSON file
- Otherwise, it will create files with placeholder values

The config files may be edited and used to generate a new PDF report.

Example:
```
mini-djerba setup
```

This will create two files, `mini_djerba.ini` and `summary.txt`, in the current working directory.

The files we have just created have placeholder values. To fill in values from a JSON report:
```
mini-djerba setup -j report.json
```

As before, we can change the output directory with `-o`:
```
mini-djerba setup  -j report.json -o /my/output/directory
```

(config=)
### Editing config files

- This can be done in any text editor, eg. [nano](https://www.nano-editor.org/), [Notepad](https://apps.microsoft.com/detail/9MSMLRH6LZF3?hl=en-US&gl=US) for Windows, [Emacs](https://www.gnu.org/software/emacs/), [Vim](https://www.vim.org/).
- Using a full-featured word processor such as MS Word is unnecessary; if doing so, output _must_ be saved in plain-text format.

#### INI file

The INI config file contains section headers in square brackets, and parameters in the form `key=value`:

```
[patient_info]
patient_name = LAST, FIRST
patient_dob = YYYY-MM-DD
patient_genetic_sex = SEX
requisitioner_email = NAME@DOMAIN.COM
physician_licence_number = nnnnnnnn
physician_name = LAST, FIRST
physician_phone_number = nnn-nnn-nnnn
hospital_name_and_address = HOSPITAL NAME AND ADDRESS

[supplement.body]
report_signoff_date = 2024-07-24
clinical_geneticist_name = Trevor Pugh, PhD, FACMG
clinical_geneticist_licence = 1027812
```

The parameters may be edited as needed. The section headers, parameter keys, and = signs must not be altered.

A config file with completed PHI will look like this (with mock values, for illustration only):
```
[patient_info]
patient_name = Doe, John
patient_dob = 1970-01-01
patient_genetic_sex = M
requisitioner_email = a.researcher@example.com
physician_licence_number = 12345678
physician_name = Smith, Jane
physician_phone_number = 555-123-4567
hospital_name_and_address = Central Hospital, Anytown

[supplement.body]
report_signoff_date = 2024-07-24
clinical_geneticist_name = Trevor Pugh, PhD, FACMG
clinical_geneticist_licence = 1027812
```

Key/value formatting conventions are derived from the Python [ConfigParser](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure) implementation.

#### TXT file

The summary text file is in plain-text format:
- [Markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet) is supported for simple formatting such as italic text
- HTML tags such as [hyperlinks](https://www.w3schools.com/tags/tag_a.asp) are supported
- Special characters (Greek letters, mathematical symbols, etc.) may be included using [HTML character entities](https://www.w3schools.com/html/html_entities.asp)
- Djerba supports the [UTF-8 character set](https://www.w3schools.com/charsets/default.asp). 

### Update to produce a new PDF

We now bring the input JSON and config files together, to produce an updated report PDF.

Example:
```
mini-djerba update -j report.json -i mini_djerba.ini -s summary.txt
```

This will write a new PDF report with _updated_ PHI and summary text. The default location for output is a PDF file in the current working directory named `[report_id].clinical.pdf`. As before, an alternate directory may be specified with the `-o` option:
```
mini-djerba update -j report.json -i mini_djerba.ini -s summary.txt -o /my/output/directory
```

If no changes are desired, either of the config files may be omitted. For example:
Example:
```
mini-djerba update -j report.json -i mini_djerba.ini
```

Note that TAR reports do not include a summary and will not accept the `-s` option.

### Additional options

For a full listing of command-line options, run with `-h`:

```
mini_djerba -h
mini_djerba setup -h
mini_djerba report -h
```

## Troubleshooting

### Types of error

There are 3 main types of error in mini-Djerba:

1. **Incorrectly formatted config files:** Check the INI and TXT formats, with reference to the [examples and links above](config), and try again.
2. **Mismatched software versions:** Mini-Djerba is a self-contained build of the Djerba software. The Djerba version used to generate the JSON input may be  _older_ or _newer_ than your copy of Mini-Djerba. If the JSON file is _too old_, Mini-Djerba will not run. If the JSON file is _newer_, it will cause a warning, which can be overridden with the `--force` option.
3. **Unexpected errors:** Mini-Djerba is tested before release, but unexpected errors may occur from time to time.

In the first two cases, `mini-djerba` will print an informative error message to the command line. In the third, the error is likely to be more technical. If in doubt, consult the Djerba developers.

### Logging

Mini-Djerba has options to write additional output to the terminal, which may be helpful in diagnosing issues. The `--verbose` option provides more output, and `--debug` even more. Either option may be specified. This _must_ be done before the option name, for example:

```
mini-djerba --verbose update -j report.json -i mini_djerba.ini -s summary.txt
```

Alternatively, for even more detail:

```
mini-djerba --debug update -j report.json -i mini_djerba.ini -s summary.txt
```

## The JSON input file

The Djerba [JSON](https://en.wikipedia.org/wiki/JSON) document is produced as part of the report drafting process by the Clinical Genome Interpretation team. It is a machine-readable file containing the data needed to produce a clinical report.

The JSON is _not_ intended to be edited by hand; mini-Djerba gets the user inputs it needs from its config files.


## For Developers

Building mini-Djerba is done with [PyInstaller](https://pyinstaller.org/en/stable/).

Detailed instructions are on the [OICR wiki](https://wiki.oicr.on.ca/x/xgBTDw).

Mini-Djerba source code is part of the [Djerba repository](https://github.com/oicr-gsi/djerba) on Github.

