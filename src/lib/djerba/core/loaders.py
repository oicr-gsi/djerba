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
"""

import importlib
import inspect
import logging
from djerba.plugins.base import plugin_base
from djerba.util.logger import logger

class plugin_loader(logger):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def load(self, plugin_name):
        try:
            plugin = importlib.import_module('djerba.plugins.{0}.plugin'.format(plugin_name))
        except ModuleNotFoundError as err:
            msg = "Cannot load plugin {0}: {1}".format(plugin_name, err)
            self.logger.error(msg)
            raise PluginLoadError from err
        # check for other errors
        if not 'main' in dir(plugin):
            msg = "Plugin {0} has no 'main' attribute".format(plugin_name)
            self.logger.error(msg)
            raise PluginLoadError(msg)
        else:
            self.logger.debug("'main' attribute of plugin {0} found".format(plugin_name))
        if not inspect.isclass(plugin.main):
            msg = "Plugin {0} main attribute is not a class".format(plugin_name)
            self.logger.error(msg)
            raise PluginLoadError(msg)
        else:
            self.logger.debug("'main' attribute of plugin {0} is a class".format(plugin_name))
        if not issubclass(plugin.main, plugin_base):
            msg = "Plugin {0} main attribute ".format(plugin_name)+\
                  "is not a subclass of djerba.plugins.base"
            self.logger.error(msg)
            raise PluginLoadError(msg)
        else:
            msg = "Plugin {0} main ".format(plugin_name)+\
                  "is a subclass of djerba.plugins.base"
            self.logger.debug(msg)
        return plugin.main(self.log_level, self.log_path)

class PluginLoadError(Exception):
    pass
