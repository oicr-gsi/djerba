"""
Base class for all components: Plugins, helpers, mergers

Defines a wide range of methods for common configuration tasks
"""

import logging
import os
import string
from abc import ABC, abstractmethod
from configparser import ConfigParser
from uuid import uuid4
from djerba.core.base import base as core_base
from djerba.util.logger import logger
import djerba.core.constants as cc
import djerba.util.ini_fields as ini

class configurable(core_base, ABC):

    """
    Interface for Djerba objects configurable by INI
    Subclasses include the core configurer, and all plugin/helper/merger classes

    Implements a number of methods, organized below as follows:
    - General-purpose methods
    - Required/default parameters and parameter validation
    - Get special directory paths from environment variables
    - Handle component priorities
    - Get/set/query INI params (other than priority levels)
    """

    # default list of known attributes -- may override in subclasses
    KNOWN_ATTRIBUTES = [
        cc.CLINICAL,
        cc.SUPPLEMENTARY,
        cc.RESEARCH,
        cc.FAILED
    ]

    def __init__(self, **kwargs):
        self.identifier = kwargs[cc.IDENTIFIER]
        self.module_dir = kwargs[cc.MODULE_DIR]
        self.log_level = kwargs[cc.LOG_LEVEL]
        self.log_path = kwargs[cc.LOG_PATH]
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        self.ini_required = set() # names of INI parameters the user must supply
        self.ini_defaults = {} # names and default values for other INI parameters

    def _raise_unknown_config_error(self, key, complete=True):
        mode = 'fully-specified' if complete else 'minimal'
        template = "Unknown INI parameter '{0}' in {1} config of component {2}. "+\
            "Required = {3}, Defaults = {4}"
        params = (key, mode, self.identifier, self.ini_required, self.ini_defaults)
        msg = template.format(*params)
        self.logger.error(msg)
        raise DjerbaConfigError(msg)

    def _raise_missing_config_error(self, key, input_keys, complete=True):
        mode = 'fully-specified' if complete else 'minimal'
        template = "Key '{0}' required for {1} config "+\
            "of component {2} was not found in inputs {3}"
        msg = template.format(key, mode, self.identifier, input_keys)
        self.logger.error(msg)
        raise DjerbaConfigError(msg)

    def _raise_null_param_error(self, key):
        msg = "INI section {0}, option {1} is null; ".format(self.identifier, key)+\
            "null values are not permitted in fully-specified Djerba config"
        self.logger.error(msg)
        raise DjerbaConfigError(msg)

    def check_attributes_known(self, attributes):
        all_known = True
        for a in attributes:
            if not a in self.KNOWN_ATTRIBUTES:
                self.logger.warning("Unknown attribute '{0}' in config".format(a))
                all_known = False
        return all_known

    def configure(self, config):
        """Input/output is a ConfigParser object"""
        self.logger.debug("Superclass configure method; only applies defaults (if any)")
        config = self.apply_defaults(config)
        return config

    def get_config_wrapper(self, config):
        return config_wrapper(config, self.identifier, self.log_level, self.log_path)

    def get_module_dir(self):
        return self.module_dir

    def get_identifier(self):
        return self.identifier

    def get_reserved_default(self, param):
        # get the default value of a reserved parameter
        # raise an error if it is not defined for the current component
        msg = None
        if not param in cc.RESERVED_PARAMS:
            msg = "'{0}' is not a reserved parameter".format(param)
        elif not param in self.ini_defaults:
            msg = "'{0}' not found in INI defaults {1}; ".format(param, self.ini_defaults)+\
                "maybe parameter is not defined for this component type?"
        if msg:
            self.logger.error(msg)
            raise DjerbaConfigError(msg)
        return self.ini_defaults[param]

    def set_log_level(self, level):
        # use to change the log level set by the component loader, eg. for testing
        self.logger.setLevel(level)

    @abstractmethod
    def specify_params(self):
        self.logger.warning("Abstract specify_params not intended to be called")

    #################################################################
    ### start of methods to handle required/default parameters

    def add_ini_discovered(self, key):
        """
        Add a 'discovered' parameter to be filled in at runtime by custom config code
        Do this by setting a null default value
        """
        self.set_ini_default(key, cc.NULL)

    def add_ini_required(self, key):
        if key in cc.RESERVED_PARAMS:
            msg = 'Cannot add reserved key {0} as a required parameter'.format(key)
            self.logger.error(msg)
            raise DjerbaConfigError(msg)
        elif key in self.ini_defaults:
            msg = 'Cannot add {0} as required parameter; '.format(key)+\
                'already exists as default'
            self.logger.error(msg)
            raise DjerbaConfigError(msg)
        elif key in self.ini_required:
            msg = 'Redundant addition of required parameter: {0}'.format(key)
            self.logger.warning(msg)
        else:
            self.ini_required.add(key)

    def apply_defaults(self, config):
        """
        Apply default parameters to the given ConfigParser
        This method does not overwrite existing values
        """
        for key in self.ini_defaults:
            if not config.has_option(self.identifier, key):
                config.set(self.identifier, key, str(self.ini_defaults[key]))
        return config

    def get_all_expected_ini(self):
        # returns a set of all expected INI parameter names
        return self.ini_required.union(set(self.ini_defaults.keys()))

    def get_expected_config(self, compact=False):
        """
        Return a ConfigParser with all expected params
        Params are set to their default values, if any; None otherwise
        Template substitution is *not* done here
        Can use to generate a config file for manual completion
        """
        config = ConfigParser()
        config.add_section(self.identifier)
        for option in sorted(list(self.ini_required)):
            config.set(self.identifier, option, 'REQUIRED')
        if not compact:
            for option in sorted(list(self.ini_defaults.keys())):
                config.set(self.identifier, option, str(self.ini_defaults[option]))
        return config

    def set_ini_default(self, key, value):
        msg = None
        if key in self.ini_required:
            msg = 'Cannot set default for {0}; '.format(key)+\
                'already exists as a required parameter'
        elif key in cc.RESERVED_PARAMS and not key in self.ini_defaults:
            msg = "Cannot set default for reserved parameter {0} ".format(key)+\
                "as it is not defined for this component type"
        if msg:
            self.logger.error(msg)
            raise DjerbaConfigError(msg)
        self.ini_defaults[key] = value

    @abstractmethod
    def set_priority_defaults(self, priority):
        # convenience method to set all priority defaults to the given value
        # which priorities are defined depends if plugin, helper, or merger
        self.logger.warning("Abstract set_priority_defaults not intended to be called")

    def update_wrapper_if_null(self, wrapper, file_name, config_key, json_key=None):
        """If parameter is null, attempt to read from workspace JSON"""
        if json_key == None:
            json_key = config_key
        if wrapper.my_param_is_null(config_key):
            if self.workspace.has_file(file_name):
                data = self.workspace.read_json(file_name)
                try:
                    value = data[json_key]
                except KeyError as err:
                    msg = "Cannot find {0} in workspace file {1}".format(json_key, file_name)
                    self.logger.error(msg)
                    raise DjerbaConfigError(msg) from err
                wrapper.set_my_param(config_key, value)
            else:
                msg = "Cannot find {0}; must be manually specified ".format(config_key)+\
                    "or given in workspace {0}".format(file_name)
                self.logger.error(msg)
                raise DjerbaConfigError(msg)
        return wrapper

    def validate_minimal_config(self, config):
        """Check for required/unknown config keys in minimal config"""
        self.logger.info("Validating minimal config for component "+self.identifier)
        input_keys = config.options(self.identifier)
        for key in self.ini_required:
            if key not in input_keys:
                self._raise_missing_config_error(key, input_keys, complete=False)
        for key in input_keys:
            if key not in self.ini_required and key not in self.ini_defaults:
                self._raise_unknown_config_error(key, complete=False)
        self.validate_priorities(config)
        return config

    def validate_full_config(self, config):
        """Check that all config keys (both required and optional) are present"""
        self.logger.info("Validating fully-specified config for component "+self.identifier)
        all_keys = self.get_all_expected_ini()
        template = "{0} expected INI param(s) found for component {1}"
        self.logger.debug(template.format(len(all_keys), self.identifier))
        input_keys = config.options(self.identifier)
        for key in all_keys:
            # Check all keys defined for the component are present and non-null
            if key not in input_keys:
                self._raise_missing_config_error(key, input_keys, complete=True)
            elif self._is_null(config.get(self.identifier, key)):
                self._raise_null_param_error(key)
        for key in input_keys:
            # Check if any keys input are *not* defined for the component
            if key not in all_keys:
                self._raise_unknown_config_error(key, complete=True)
        self.validate_priorities(config)
        return config

    def validate_priorities(self, config):
        # check priorities are non-negative integers
        # TODO sanity checking on other reserved params
        ok = True
        for s in config.sections():
            for p in cc.PRIORITY_KEYS:
                if config.has_option(s, p):
                    try:
                        v = config.getint(s, p)
                    except ValueError:
                        ok = False
                    if v < 0:
                        ok = False
                if not ok:
                    msg = "{0}:{1} must be a non-negative integer; got {2}".format(s, p, v)
                    self.logger.error(msg)
                    raise ValueError(msg)
        return config

class core_configurer(configurable):

    """Class to do core configuration"""

    PRIORITY = 100

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workspace = kwargs['workspace']
        self.ini_defaults = {
            cc.ATTRIBUTES: '',
            cc.DEPENDS_CONFIGURE: '',
            cc.DEPENDS_EXTRACT: '',
            cc.CONFIGURE_PRIORITY: self.PRIORITY,
            cc.EXTRACT_PRIORITY: self.PRIORITY,
            cc.RENDER_PRIORITY: self.PRIORITY
        }
        self.specify_params()

    def configure(self, config):
        """Input/output is a ConfigParser object"""
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        if wrapper.my_param_is_null(cc.REPORT_ID):
            sample_info_file = wrapper.get_my_string(cc.SAMPLE_INFO)
            if self.workspace.has_file(sample_info_file):
                sample_info = self.workspace.read_json(sample_info_file)
                report_id = "{0}-v{1}".format(
                    sample_info[cc.TUMOUR_ID],
                    wrapper.get_my_int(cc.REPORT_VERSION)
                )
                msg = "Generated report ID {0} from sample info JSON".format(report_id)
                self.logger.debug(msg)
            else:
                report_id = "OICR-CGI-{0}".format(uuid4().hex)
                msg = "Generated report ID {0} from UUID hex string".format(report_id)
                self.logger.debug(msg)
            wrapper.set_my_param(cc.REPORT_ID, report_id)
        return wrapper.get_config()

    def specify_params(self):
        self.add_ini_discovered(cc.REPORT_ID)
        self.set_ini_default(cc.REPORT_VERSION, 1)
        self.set_ini_default(cc.ARCHIVE_NAME, "djerba")
        self.set_ini_default(
            cc.ARCHIVE_URL,
            "http://${username}:${password}@${address}:${port}"
        )
        self.set_ini_default(cc.AUTHOR, cc.DEFAULT_AUTHOR)
        self.set_ini_default(cc.SAMPLE_INFO, cc.DEFAULT_SAMPLE_INFO)
        self.set_ini_default(cc.DOCUMENT_CONFIG, cc.DEFAULT_DOCUMENT_CONFIG)

    def set_priority_defaults(self, priority):
        for key in cc.PRIORITY_KEYS:
            self.ini_defaults[key] = priority


class config_wrapper(core_base):

    """Wrapper for a ConfigParser object with convenience methods"""

    def __init__(self, config, identifier, log_level=logging.WARNING, log_path=None):
        # config is a ConfigParser object
        # identifier is the component identifier, used to retrieve INI params
        self.config = config
        self.identifier = identifier
        self.logger = self.get_logger(log_level, __name__, log_path)

    def get_config(self):
        return self.config

    #################################################################
    ### start of methods to get/set/query INI params (other than priority levels)

    def get_core_string(self, param):
        return self.config.get(ini.CORE, param)

    def get_core_int(self, param):
        return self.config.getint(ini.CORE, param)

    def get_core_float(self, param):
        return self.config.getfloat(ini.CORE, param)

    def get_core_boolean(self, param):
        return self.config.getboolean(ini.CORE, param)

    # no set_core_param() -- components only write their own INI section

    def get_my_attributes(self):
        if self.has_my_param(cc.ATTRIBUTES):
            attributes_str = self.get_my_string(cc.ATTRIBUTES)
            attributes = self._parse_comma_separated_list(attributes_str)
        else:
            attributes = []
        return attributes

    # nullity tests

    def my_param_is_null(self, param):
        return self.param_is_null(self.identifier, param)

    def param_is_null(self, section, param):
        return self._is_null(self.config.get(section, param))

    def my_param_is_not_null(self, param):
        return not self.my_param_is_null(param)

    def param_is_not_null(self, section, param):
        return not self.param_is_null(section, param)

    # [get|set|has]_my_* methods for the named component

    def get_my_boolean(self, param):
        return self.config.getboolean(self.identifier, param)

    def get_my_float(self, param):
        return self.config.getfloat(self.identifier, param)

    def get_my_int(self, param):
        return self.config.getint(self.identifier, param)

    def get_my_string(self, param):
        return self.config.get(self.identifier, param)

    def has_my_param(self, param):
        return self.config.has_option(self.identifier, param)

    def get_my_priorities(self):
        """
        Find configure/extract/render priorities, if any
        extract and render are not defined for mergers and helpers, respectively
        Used at extract step to convert INI settings into JSON
        """
        priorities = {}
        mapping = {
            cc.CONFIGURE_PRIORITY: cc.CONFIGURE,
            cc.EXTRACT_PRIORITY: cc.EXTRACT,
            cc.RENDER_PRIORITY: cc.RENDER
        }
        for key, value in mapping.items():
            if self.config.has_option(self.identifier, key):
                priorities[value] = self.config.getint(self.identifier, key)
        return priorities

    def set_my_priorities(self, priority):
        # convenience method; sets all defined priorities to the same value
        for key in cc.PRIORITY_KEYS:
            if self.has_my_param(key):
                self.set_my_param(key, priority)

    def set_my_param(self, param, value):
        self.config.set(self.identifier, param, str(value))

    # [get|set|has]_my_* methods for other components

    def get_boolean(self, section, param):
        return self.config.getboolean(section, param)

    def get_float(self, section, param):
        return self.config.getfloat(section, param)

    def get_int(self, section, param):
        return self.config.getint(section, param)

    def get(self, section, param):
        # alias for get_string, to be consistent with ConfigParser interface
        return self.get_string(section, param)

    def get_string(self, section, param):
        return self.config.get(section, param)

    def has_option(self, section, param):
        # alias for has_param, to be consistent with ConfigParser interface
        return self.has_param(section, param)

    def has_param(self, section, param):
        return self.config.has_option(section, param)

    def set_param(self, section, param, value):
        self.config.set(section, param, str(value))

    def set(self, section, param, value):
        # alias for set_param, to be consistent with ConfigParser interface
        self.set_param(section, param, value)


class DjerbaConfigError(Exception):
    pass
