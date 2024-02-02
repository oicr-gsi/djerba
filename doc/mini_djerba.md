
# Mini-Djerba

## Introduction

Mini-Djerba allows a clinical geneticist to update personal health information (PHI) and edit the results summary in a Djerba report.

Input to mini-djerba is a file in [JSON format](https://en.wikipedia.org/wiki/JSON) containing clinical report data. Filenames are typically of the form `[report_id].json`, eg. `100-009-005_LCM3-v1_report.json`.

Steps are as follows:
1. Render an initial PDF file for inspection
2. Generate a config file
3. Edit the config file with PHI values and summary text
4. Use the config file to generate a new PDF with the updated PHI and summary

Mini-Djerba is distributed as a single, executable file. It is a command-line application; run with `-h` for help.

In brief, usage is `mini-djerba [mode] [options]`

Available modes are:
- `render`: Make a PDF from JSON input, without any changes
- `setup`: Generate a config file to be updated by the user
- `update`: Use the JSON input and config file to generate an *updated* PDF document

## Usage

### 1. Render initial PDF

The `render` mode converts a JSON document to PDF format. In other words, it goes from the machine-readable format to human-readable.

Example:

```
mini-djerba render -j report.json
```

The default location for output is a PDF file in the current working directory named `[report_id].json`.

### 2. Generate config file

The config file is in MDC (mini-Djerba config) format. This is a simple text-based format defined for mini-Djerba. See [MDC format](#mdc_format) for details.

The file is generated in `setup` mode. The `-j` option inserts summary text drafted by a genome interpreter, for subsequent editing. Running without `-j` produces a "blank" MDC file.

Example:
```
mini-djerba setup -j report.json
```

### 3. Edit the config file with PHI values and summary text

- This can be done in any text editor, eg. [nano](https://www.nano-editor.org/), [Notepad](https://apps.microsoft.com/detail/9MSMLRH6LZF3?hl=en-US&gl=US) for Windows, [Emacs](https://www.gnu.org/software/emacs/), [Vim](https://www.vim.org/).
- Using a full-featured word processor such as MS Word is unnecessary; if doing so, output must be saved in plain-text format.
- See [MDC format](#mdc_format) for details and an example config file.

### 4. Update to produce a new PDF

We now bring the input PDF and config file together, to produce an updated report PDF.

Example:
```
mini-djerba update -j report.json -c config.mdc
```

This will write a new JSON file with _updated_ PHI and summary text. The default location for output is a PDF file in the current working directory named `[report_id].json`.

Note the default is the same as for the `render` option in Step 1, so it may overwrite the previous output -- but this should not be an issue, as the PDF generated in this step is the version to be uploaded for clinical use.

### Additional options

For a full listing of command-line options, run with `-h`:

```
mini_djerba -h
mini_djerba render -h
mini_djerba setup -h
mini_djerba update -h
```

## Troubleshooting

There are 3 main types of error in mini-Djerba:

1. **Incorrectly formatted MDC file:** Check the [MDC documentation](#mdc_format) and try again.
2. **Mismatched plugin versions:** Mini-Djerba is built with a self-contained set of Djerba plugins. A Djerba JSON report may have been generated with _newer_ plugin versions than the ones in mini-Djerba; this is cause for a warning, which can be overridden with the `--force` option. Running with mismatched plugin versions will _usually_ work correctly, but may result in errors. Alternatively, upgrade to a newer version of mini-Djerba.
3. **Unexpected errors:** Mini-Djerba is tested before release, but unexpected errors may occur from time to time.

In the first two cases, `mini-djerba` will print an informative error message to the command line. In the third, the error is likely to be more technical. If in doubt, consult the Djerba developers.

<a name="mdc_format"></a>
## The Mini-Djerba config file

MDC files (mini-Djerba config, file extension `.mdc`) specify the PHI and summary in a compact, text-based format. It is a simple, text-based format developed for Mini-Djerba.

### MDC example

Here is an example MDC file with placeholder values:

```
patient_name = LAST, FIRST
patient_dob = yyyy/mm/dd
patient_genetic_sex = SEX
requisitioner_email = NAME@domain.com
physician_licence_number = nnnnnnnn
physician_name = LAST, FIRST
physician_phone_number = nnn-nnn-nnnn
hospital_name_and_address = HOSPITAL NAME AND ADDRESS

###

[Lorem ipsum dolor](https://www.lipsum.com/) sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

```

### MDC Format Specification: Version 1.0

The following elements _must_ appear in this order:
1. A section with exactly 8 entries of the form `key = value`
2. A separator consisting of 3 hash marks: `###`
3. Summary text

The 8 entries correspond to the 8 PHI fields listed above:
1. `patient_name`
2. `patient_dob`
3. `patient_genetic_sex`
4. `requisitioner_email`
5. `physician_licence_number`
6. `physician_name`
7. `physician_phone_number`
8. `hospital_name_and_address`

These entries may occur in any order, but _must_ be present and have non-empty values.

Summary text must be non-empty. Leading or trailing whitespace will be removed before the text is inserted into the report; but whitespace, including line breaks, may occur within the text block. Formatting with [Markdown notation](https://www.markdownguide.org/cheat-sheet/) and/or HTML tags is supported. This enables the user to create or edit bold/italic text, hyperlinks, etc.

## The JSON input file

The Djerba [JSON](https://en.wikipedia.org/wiki/JSON) document is produced as part of the report drafting process by the Clinical Genome Interpretation team. It is a machine-readable file containing the data needed to produce a clinical report.

The JSON is _not_ intended to be edited by hand; mini-Djerba gets the user inputs it needs from the MDC file.


## For Developers

### Build instructions

Building mini-Djerba is done with [PyInstaller](https://pyinstaller.org/en/stable/).

Detailed instructions are on the [OICR wiki](https://wiki.oicr.on.ca/x/xgBTDw).

### Technical notes

Key/value parsing is done with the Python [configparser](https://docs.python.org/3/library/configparser.html) package and has similar formatting conventions.

The MDC file format is implemented in Djerba as the [mdc class](https://github.com/oicr-gsi/djerba/blob/main/src/lib/djerba/util/mini/mdc.py#L14).

Tests are in the [TestMDC class](https://github.com/oicr-gsi/djerba/blob/main/src/test/util/mini/test_mini.py#L16).
