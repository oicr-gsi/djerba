(how_djerba_works)=

# How Djerba Works

## File Formats

Djerba uses four main file formats:
- INI: simple plain-text configuration file
- JSON: Machine-readable file with report data
- HTML: Data transformed into a human-readable format
- PDF: Self-contained document for sharing and archiving

## Production Steps

Report production in Djerba has three basic steps: Configure, Extract, and Render.

| Step | Input | Output | Description |
| :---- | :---- | :---- | :---- |
| Configure | INI (partial) | INI (complete) | Populate all configuration parameters, using defaults and/or automated queries |
| Extract | INI (complete) | JSON | Process inputs to generate data for the report |
| Render | JSON | HTML, PDF | Use the JSON data to write a human-readable HTML document, which is then converted to PDF |

**Table 1:** Steps of Djerba report generation

## The `djerba.py` Script

The main user interface for Djerba is a command-line script, `djerba.py`.

The `djerba.py` script has a number of subcommands or *modes* to set up and run the configure, extract, and render operations (Table 2). A user will typically run “setup” to generate an initial configuration file; “report” to generate a first draft PDF document for inspection; and “update” as needed to refine the PDF until it is ready for release. The intermediate output in JSON format provides a machine-readable version of all data needed to make the report, and may be saved for future reference. Djerba supports automated upload of the JSON report to a CouchDB database instance.

| Mode | Input | Output | Description |
| :---- | :---- | :---- | :---- |
| setup | Name of assay | Partial INI file | Create a minimal INI file to be completed by the user |
| configure | Partial INI file | Fully specified INI file | Fill in configuration parameters |
| extract | Fully specified INI file | JSON file | Process and annotate inputs to generate data for the report |
| render | JSON file | HTML with optional PDF | Transform JSON into a human readable HTML or PDF with tables, plots, etc. |
| report | Partial INI file | JSON, HTML, and PDF | Combine the configure, extract, and render operations |
| update | JSON file; partial INI file or summary text | JSON, HTML, and PDF | Re-run the extract and render operations for selected components, regenerating the HTML and PDF outputs |

**Table 2**: Modes of the `djerba.py` command-line script

See the [user guide](user_guide_FIXME) for command-line syntax and options.

## Modular Components

The architecture of Djerba is modular, enabling the report to be rapidly adapted to changing circumstances. Modular units of Djerba are known as *components*. Report components can be added, removed, or modified as needed. Each component can be run as a self-contained unit, to facilitate rapid testing and development. Components can read and write files in a shared *workspace*, allowing the supply of information from one component to another.

The INI configuration file is divided into named sections; each section represents a component. Djerba has the following types of component:

* **Core**, the central element of Djerba and required in every report. The core is responsible for loading and executing other components in the correct order. It also sets certain report-wide parameters such as the name of the interpreter.  
* **Plugins** are the main components used to generate the report. A plugin uses its INI configuration section to generate a JSON object conforming to a defined schema; and converts the JSON into HTML. Each plugin generates its own section of HTML; the combined HTML document is converted to PDF by the core. A plugin has **configure**, **extract**, and **render** methods which correspond to modes of the same name in Table 1\.  
* **Helpers** do not produce HTML output, but can write to the workspace. They are principally used to gather operating parameters, which may then be distributed to multiple plugins.  
* **Mergers** take the output of multiple plugins, remove duplicates, and generate HTML output which is later converted to PDF. They are used to generate summaries of therapies or genes identified by plugins.
