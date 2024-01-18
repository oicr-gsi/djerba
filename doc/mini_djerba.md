# Mini-Djerba

## Introduction

Mini-Djerba allows clinical geneticists to update personal health information (PHI) and edit the results summary in a Djerba report.

Steps are as follows:
1. Generate a config file in MDC format
2. Edit the MDC file with PHI values and summary text
3. Use the MDC file to generate a PDF with the updated PHI and summary

Mini-Djerba is distributed as a single, executable file. It is a command-line application; run with `-h` for help.

## MDC: Mini-Djerba Config format

MDC files (mini-Djerba config, file extension `.mdc`) specify the PHI and summary in a compact, text-based format.

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

[Lorem ipsum dolor](https://www.lipsum.com/) sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

```

### Format specification

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

Summary text must be non-empty. Leading or trailing whitespace will be removed before the text is inserted into the report; but whitespace, including line breaks, may occur within the text block. Formatting with [Markdown notation](https://www.markdownguide.org/cheat-sheet/) and/or HTML tags is supported.

## Usage

Using Mini-Djerba consists of two steps:
1. *Ready:* Read an input JSON file and generate the MDC
2. *Update:* Edit the MDC as needed, and produce HTML and PDF output

### The input JSON

The Djerba JSON document is produced as part of the report drafting process by the Clinical Genome Interpretation team. It is a machine-readable file containing the data needed to produce a clinical report. It is _not_ intended to be edited by hand; mini-Djerba gets the user inputs it needs from the MDC file.

### Ready step

ready

### Update step

update


## For Developers

### Build instructions

Building mini-Djerba is done with [PyInstaller](https://pyinstaller.org/en/stable/).

### Technical notes

Key/value parsing is done with the Python [configparser](https://docs.python.org/3/library/configparser.html) package and has similar formatting conventions, except no section headers are needed.

The MDC file format is implemented in Djerba as the [mdc class](https://github.com/oicr-gsi/djerba/blob/main/src/lib/djerba/util/mini/mdc.py#L14).

Tests are in the [TestMDC class](https://github.com/oicr-gsi/djerba/blob/main/src/test/util/mini/test_mini.py#L16).

