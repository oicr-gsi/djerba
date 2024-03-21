"""
Import a named plugin and make an instance of it

Plugin identifiers:
- *Must* be the headers of the corresponding INI sections
- *Must* identify submodules of djerba.plugins
- *Must not* be the string `core` or `base`
- *May* contain additional levels, eg. name `foo.bar` -> djerba.plugins.foo.bar
- May originate from INI, JSON, or elsewhere (eg. a test script)
- Differ from `plugin name` in the schema, a human-readable value which can be anything

Plugin modules:
- *Must* have a module `plugin.py` with a class `main`
- The `main` class *must* be a subclass of `djerba.plugins.base.plugin_base`
- The `main` class *must not* have an __init__() method overriding the superclass
- The `main` class *must* have `configure`, `extract`, `render` methods
- configure *must* input an ConfigParser section, output a ConfigParser section
- extract *must* input a ConfigParser section; output data satisfying the plugin schema
- render *must* input data matching the plugin schema, output a string

Merger modules are similar, but:
- *Must* have a module `merger.py` with a class `main`
- Only need a `render` method

Helper modules are similar, but:
- *Must* have a module `helper.py` with a class `main`
- Only need `configure` and `extract` methods

The DJERBA_PACKAGES environment variable lists allowed top-level package names
- Defaults to the name `djerba`
- May include multiple names separated by colons
- Top-level package names are resolved from left to right
- Djerba attempts to import from each package name in order
- Failure to find a named component in any top-level package raises an error
"""

import importlib
import inspect
import logging
import os
import re
from abc import ABC
from djerba.core.base import base as core_base
from djerba.plugins.base import plugin_base
from djerba.mergers.base import merger_base
from djerba.helpers.base import helper_base
import djerba.core.configure as core_configure
import djerba.core.constants as core_constants

class loader_base(core_base, ABC):

    PLUGIN = 'plugin'
    MERGER = 'merger'
    HELPER = 'helper'

    DJERBA_PACKAGES = 'DJERBA_PACKAGES'
    DJERBA_PACKAGES_DEFAULT = ['djerba', ]

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.packages = self.resolve_top_packages()

    def get_common_args(self, module_name, module):
        """Get the constructor args common to all component types"""
        module_dir = os.path.abspath(os.path.dirname(module.__file__))
        args = {
            core_constants.IDENTIFIER: module_name,
            core_constants.MODULE_DIR: module_dir,
            core_constants.LOG_LEVEL: self.log_level,
            core_constants.LOG_PATH: self.log_path
        }
        return args

    def import_module(self, module_type, name):
        permitted = [self.PLUGIN, self.MERGER, self.HELPER]
        if module_type not in permitted:
            msg = "Module type {0} not in permitted list {1}".format(
                module_type,
                permitted
            )
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        # full name for import is eg. djerba.plugins.cnv.plugin
        # check each top-level package in turn
        # use the first one with a valid import spec; if none found, raise an error
        package_for_import = None
        for package in self.packages:
            # work down the hierarchy of package names
            # do it this way to avoid an ImportError when checking non-existent package
            hierarchy = [package, module_type+'s', name, module_type]
            levels = []
            package_ok = True
            for level in hierarchy:
                levels.append(level)
                if importlib.util.find_spec('.'.join(levels)) == None:
                    package_ok = False
                    break
            if package_ok:
                package_for_import = package
                break
        if package_for_import:
            try:
                args = [package_for_import, module_type, name]
                full_name = '{0}.{1}s.{2}.{1}'.format(*args)
                module = importlib.import_module(full_name)
            except Exception as err:
                msg = "Cannot load {0}.{1}s.{2}.{1}: {3}".format(*args, err)
                self.logger.error(msg)
                raise DjerbaLoadError from err
        else:
            msg = "Cannot load module {0} of type {1}; ".format(name, module_type)+\
                "no valid spec in top-level DJERBA_PACKAGES: {0}".format(self.packages)
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        return module

    def instantiate_main(self, module, args):
        # do some error checking and return an instance of the main class
        try:
            main_object = module.main(**args)
        except TypeError as err:
            msg = "Error loading component. Maybe specify_params() is not defined?"
            self.logger.error("{0} {1}".format(msg, err))
            raise DjerbaLoadError(msg) from err
        return main_object

    def load(self):
        msg = "Attempting to call placeholder method of base loader class; "+\
            "must be overridden in subclasses"
        self.logger.error(msg)
        raise DjerbaLoadError(msg)

    def resolve_top_packages(self):
        # find top-level package names from environment variable, or use default
        if self.DJERBA_PACKAGES in os.environ:
            packages = re.split(':', os.environ.get(self.DJERBA_PACKAGES))
            for p in packages:
                # check if package names are valid Python identifiers
                # does *not* check if they can be imported; this is done later
                if not p.isidentifier():
                    msg = 'Package name "{0}" is not a valid Python identifier; '.format(p)+\
                        'incorrectly configured {1} variable'.format(self.DJERBA_PACKAGES)
                    self.logger.error(msg)
                    raise DjerbaLoadError(msg)
            self.logger.debug("Found Djerba packages: {0}".format(packages))
        else:
            packages = self.DJERBA_PACKAGES_DEFAULT
            self.logger.debug(self.DJERBA_PACKAGES+' not configured, defaulting to "djerba"')
        return packages

    def validate_module(self, module, module_type, module_name):
        args = [module_type, module_name]
        if not 'main' in dir(module):
            msg = "{0} {1} has no 'main' attribute".format(*args)
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        if not inspect.isclass(module.main):
            msg = "{0} {1} main attribute is not a class".format(*args)
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        self.validate_module_type_and_name(module_type, module_name)
        if module_type == self.PLUGIN:
            base_class = plugin_base
        elif module_type == self.MERGER:
            base_class = merger_base
        elif module_type == self.HELPER:
            base_class = helper_base
        if not issubclass(module.main, base_class):
            msg = "{0} {1} main attribute ".format(*args)+\
                  "is not a subclass of djerba.{0}s.base".format(module_type)
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        self.logger.debug("Module {0} of type {1} is OK".format(module_name, module_type))

    def validate_module_type_and_name(self, module_type, module_name):
        msg = None
        if module_type == self.PLUGIN:
            if self._is_helper_name(module_name):
                msg = "Plugin name '{0}' ".format(module_name)+\
                    "has the format of a helper name, cannot load"
            elif self._is_merger_name(module_name):
                msg = "Plugin name '{0}' ".format(module_name)+\
                    "has the format of a merger name, cannot load"
        elif module_type == self.MERGER:
            if not self._is_merger_name(module_name):
                msg = "'{0}' is not in merger name format, cannot load".format(module_name)
        elif module_type == self.HELPER:
            if not self._is_helper_name(module_name):
                msg = "'{0}' is not in helper name format, cannot load".format(module_name)
        else:
            msg = "Cannot validate unknown module type: {0}".format(module_type)
        if msg:
            self.logger.error(msg)
            raise DjerbaLoadError(msg)

class core_config_loader(loader_base):

    # very simple, but we define a loader class for consistency with other components

    def load(self, workspace):
        # make an instance of the core configurer
        args = self.get_common_args(core_constants.CORE, core_configure)
        args[core_constants.WORKSPACE] = workspace
        return core_configure.core_configurer(**args)

class merger_loader(loader_base):

    def load(self, module_name):
        # import, validate, and make an instance of a merger
        module = self.import_module(self.MERGER, module_name)
        self.validate_module(module, self.MERGER, module_name)
        args = self.get_common_args(module_name, module)
        return self.instantiate_main(module, args)

class plugin_loader(loader_base):

    def load(self, module_name, workspace):
        # import, validate, and make an instance of a plugin with a workspace
        module = self.import_module(self.PLUGIN, module_name)
        self.validate_module(module, self.PLUGIN, module_name)
        args = self.get_common_args(module_name, module)
        args[core_constants.WORKSPACE] = workspace
        return self.instantiate_main(module, args)

class helper_loader(loader_base):

    def load(self, module_name, workspace):
        # import, validate, and make an instance of a helper with a workspace
        module = self.import_module(self.HELPER, module_name)
        self.validate_module(module, self.HELPER, module_name)
        args = self.get_common_args(module_name, module)
        args[core_constants.WORKSPACE] = workspace
        return self.instantiate_main(module, args)


class DjerbaLoadError(Exception):
    pass
