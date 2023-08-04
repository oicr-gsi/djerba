# Plugin Developer's Guide

This document is meant as a compact guide to writing plugins, and documents some tools provided by Djerba to make plugins more compact and easier to develop.

## Plugin requirements

A plugin _must_ inherit from the plugin base class: `src/lib/djerba/plugins/base.py`

A plugin _must not_ override its `__init__` constructor method, unless it uses `super().__init__` to call the superclass constructor.

A plugin _may_ override the following methods of the parent class:
- `configure`
- `extract`
- `render`
- `specify_params`

These methods are discussed in the "Key methods of plugins" section below. In order for the plugin to do anything useful, it will have to override at least one of the above methods, and usually all of them.

A plugin _may_ be more than one level of inheritance removed from the plugin base class, eg. plugins may be subclasses of other plugins.

## Key methods of plugins

The `configure`, `extract`, and `render` methods implement the three main steps of Djerba report generation.

The `specify_params` method can be thought of as a "pre-configure" step, in which we define the expected parameters and any default values.

### `configure`

This step populates configuration parameters in the INI file. Djerba defines three different parameter types:
- **Required**: Must be supplied by the user at the `configure` step
- **Default**: Has a simple default value
- **Discovered**: Populated by the `configure` method at runtime

The names of required, default, and discovered parameters are defined in the `specify_params` method. The role of the `configure` method is to populate them as needed:

- **Required**: Do nothing; the value has been supplied by the user. Appropriate checks on this are run by the Djerba core.
- **Default**: Call the `apply_defaults` method to apply all defaults
- **Discovered**: Whatever customized code is necessary: HTTP request to a server, reading a JSON file, computations to find a numerical threshold, etc.

**IMPORTANT DJERBA CONVENTION:** If the user explicitly supplies a value for a "discovered" or "default" parameter, the `configure` method _must_ apply the user-supplied value. In other words, the user can _always_ override automated defaults/discovery of a parameter by specifying it manually. Adhering to this convention is the developer's responsibility.

If a discovered parameter is _not_ specified by the user, it will be initialized to a special null value; null status can be checked using `my_param_is_null` and similar methods.

- Input: ConfigParser representing with (at least) the minimal set of parameters
- Output: ConfigParser with a fully specified set of parameters

### `extract`

This step generates metrics, tables, plots, etc. for the given INI configuration, and outputs them in JSON format. The `get_starting_data` method can be used to get a "blank" data structure to be populated.

- Input: ConfigParser with a fully specified set of parameters
- Output: Data structure conforming to the plugin JSON schema

### `render`

This step takes the JSON generated in the `extract` step, and renders it to HTML. Typically this is done using [Mako templates](https://www.makotemplates.org/); the `djerba.util` package has code to support use of Mako.

- Input: Data structure conforming to the plugin JSON schema
- Output: String for inclusion in an HTML document. May include HTML tags, base64-encoded graphics, etc.

### `specify_params`

Specify parameters for the plugin's INI config file.

It does so by calling one or more of these methods of the parent class:
- add_ini_required
- add_ini_discovered
- set_ini_default

These methods respectively correspond to the required, discovered, and default parameter types in Djerba. See "Other useful methods of plugins" for further details.

- Input: None
- Output: None

## Other useful methods of plugins

The following are methods of the plugin superclasses (plugin base and its parent class `configurable`) intended for use by plugin developers.

Unless otherwise stated, these apply to all objects which inherit from the `configurable` class -- including helpers and mergers, not just plugins.

### `get_starting_data`

Get an data structure which satisfies the plugin JSON schema, for use in the extract step. It has empty `results` and `merge_inputs` dictionaries, to be populated at runtime. Defined for plugins only, not helpers or mergers.

- *Inputs:* A `config_wrapper` object
- *Outputs:* A data structure conforming to the plugin JSON schema
- *Source code:* `src/lib/djerba/plugins/base.py`

### Other, other methods (descriptions TODO)

check_attributes_known(self, attributes):
get_config_wrapper(self, config):
get_module_dir(self):
get_identifier(self):
get_reserved_default(self, param):
set_log_level(self, level):
specify_params(self):
add_ini_discovered(self, key):
add_ini_required(self, key):
apply_defaults(self, config):
get_all_expected_ini(self):
get_expected_config(self):
set_ini_default(self, key, value):
set_priority_defaults(self, priority):
validate_minimal_config(self, config):
validate_full_config(self, config):
validate_priorities(self, config):


## Djerba configuration with INI files

The [INI file format](https://en.wikipedia.org/wiki/INI_file) is used for configuration in Djerba. It has a two-tiered structure:
- A document is split into sections, with headers in square brackets: `[section]`
- Each section has key/value pairs, separated by an equals sign: `key = value`

INI files are handled in Python with the [ConfigParser](https://docs.python.org/3/library/configparser.html) class. Python has multiple data types (string, integer, float, boolean) but the INI format does not -- in an INI file, everything is a string. Therefore, `ConfigParser` has methods to _read_ INI values as strings, integers, etc. and _write_ them as strings.

As the name suggests, the idea of the `config_wrapper` is to wrap around a `ConfigParser` object, and provide additional functionality specific to Djerba. In particular, the wrapper is aware of the name of the current plugin, and of Djerba concepts such as component priorities. The wrapper provides a number of convenience methods, which are intended to be simpler and less error-prone than manipulating a `ConfigParser` directly.

## Methods of the `config_wrapper` class

### `__init__`

Constructor for the class

#### Inputs

- `config`: A ConfigParser object
- `identifier`: The identifier of the current plugin (or helper, or merger)
- `log_level`, `log_path`: Standard logging parameters

#### Outputs

A `config_wrapper` object

---

### get_config

Get the `ConfigParser`, as modified by any methods called on the `config_wrapper` object. Useful for returning a `ConfigParser` from the `configure` method of a plugin.

- Inputs: None
- Outputs: A `ConfigParser` object

---

### get_core_string
### get_core_int
### get_core_float
### get_core_boolean

Get a parameter from the `[core]` section of the INI config. This is a reserved section containing parameters used by the Djerba core.

- Inputs: key
- Outputs: A string, int, float, or boolean, as appropriate

### get_my_attributes

Get the attributes from the INI. Attributes are represented in the INI as a comma-delimited string; this method parses them into a list.

- Inputs: None
- Outputs: List of attributes (strings)

### get_my_boolean
### get_my_float
### get_my_int
### get_my_string

Get a parameter for the current plugin.

- Inputs: key
- Outputs: Boolean, float, int, or string, as appropriate

### get_boolean
### get_float
### get_int
### get
### get_string

Similar to the respective `get_my_*` functions, but more general. Get a value of the appropriate type for the given section and key. `get` and `get_string` are identical; the former is provided for consistency with the `get` method of the `ConfigParser` class.

- Inputs: section, key
- Outputs: value

### get_my_priorities

Get the configure/extract/render priorities for the current plugin as a dictionary.

- Inputs: None
- Outputs: Dictionary

---

### my_param_is_null
### my_param_is_not_null

Check if a parameter of the current plugin is null, ie. set to the reserved null value `__DJERBA_NULL__`.

- Inputs: key
- Outputs: Boolean

### param_is_null
### param_is_not_null

As for `my_param_is_null` and `my_param_is_null`, but for any section in the INI.

- Inputs: Section name, parameter key
- Outputs: Boolean

---

### has_my_param

Check if a parameter _exists_ for the current plugin -- "does not exist" is distinct from "exists and is null".

- Inputs: key
- Outputs: Boolean

### has_option
### has_param

Identical functions to check if a parameter is present; parameters are referred to as "options" in `ConfigParser` terminology.

- Inputs: section, key
- Outputs: Boolean

---

### set_my_param

Set a parameter value for the current plugin, converting the input to a string if necessary.

- Inputs: key, value
- Outputs: None

### set_param
### set

General versions of `set_my_param`. Set the given section and option to the given value, converting it to a string if necessary. Again, the two identical names are given for consistency with both Djerba and ConfigParser terminology.

- Inputs: section, key, value
- Outputs: None

### set_my_priorities

Set all three priorities (configure, extract and render) to the same integer value.

- Inputs: Integer
- Outputs: None

---

### apply_env_templates
### apply_my_env_templates
### get_dir_from_env
### get_djerba_data_dir
### get_djerba_private_dir
### get_djerba_test_dir

Methods to do read [environment variables](https://wiki.archlinux.org/title/environment_variables) and do template substitution.

Djerba defines environment variables to configure directory paths at runtime:
- `DJERBA_DATA_DIR`
- `DJERBA_TEST_DIR`
- `DJERBA_PRIVATE_DIR`

These are intended for general-purpose data files, test data, and private information such as passwords and access keys, respectively.

The respective `get_djerba_*_dir` methods will return the value of these environment variables, if needed in plugin code.

Djerba supports the use of [string template substitution](https://docs.python.org/3/library/string.html#template-strings) for these variables in INI config. So in a config value such as `foo_path = ${DJERBA_DATA_DIR}/foo.txt`, the path can be replaced by the value of the appropriat environment variable, by calling `apply_env_templates` or `apply_my_env_templates`; these respectively take a section name as argument, and apply template substitution to the current plugin