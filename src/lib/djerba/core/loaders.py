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
"""

import importlib
import inspect
import logging
from abc import ABC
from djerba.plugins.base import plugin_base
from djerba.mergers.base import merger_base
from djerba.util.logger import logger

class loader_base(logger, ABC):


    PLUGIN = 'plugin'
    MERGER = 'merger'

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def load(self, module_type, name):
        args = [module_type, name]
        permitted = [self.PLUGIN, self.MERGER]
        if module_type not in permitted:
            msg = "Module type {0} not in permitted list {1}".format(
                module_type,
                permitted
            )
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        elif module_type == self.PLUGIN:
            base_class = plugin_base
        else:
            base_class = merger_base
        try:
            full_name = 'djerba.{0}s.{1}.{0}'.format(*args)
            module = importlib.import_module(full_name)
        except ModuleNotFoundError as err:
            msg = "Cannot load {0} {1}: {2}".format(*args, err)
            self.logger.error(msg)
            raise DjerbaLoadError from err
        # check for other errors
        if not 'main' in dir(module):
            msg = "{0} {1} has no 'main' attribute".format(*args)
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        else:
            msg = "'main' attribute of {0} {1} found".format(*args)
            self.logger.debug(msg)
        if not inspect.isclass(module.main):
            msg = "{0} {1} main attribute is not a class".format(*args)
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        else:
            msg = "'main' attribute of {0} {1} is a class".format(*args)
            self.logger.debug(msg)
        if not issubclass(module.main, base_class):
            msg = "{0} {1} main attribute ".format(*args)+\
                  "is not a subclass of djerba.{0}s.base".format(module_type)
            self.logger.error(msg)
            raise DjerbaLoadError(msg)
        else:
            msg = "{0} {1} main ".format(*args)+\
                  "is a subclass of djerba.{0}s.base".format(module_type)
            self.logger.debug(msg)
        return module.main(self.log_level, self.log_path)

class merger_loader(loader_base):

    def load(self, merger_name):
        return super().load('merger', merger_name)

class plugin_loader(loader_base):

    def load(self, plugin_name):
        return super().load('plugin', plugin_name)

class DjerbaLoadError(Exception):
    pass
