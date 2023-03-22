"""Class to test that a plugin correctly implements the API"""

from configparser import Error as ConfigParserError
import logging
import json
import djerba.util.ini_fields as ini
from djerba.core.json_validator import json_validator
from djerba.core.main import main as core_main
from djerba.core.plugin_loader import plugin_loader
from djerba.plugins.base import plugin_base
from djerba.util.logger import logger
from djerba.util.validator import path_validator


class plugin_tester(core_main):

    def run(self, config_path, plugin_name_supplied=None):
        plugin_ok = True
        self.logger.info("Reading INI path {0}".format(config_path))
        try:
            config = self.read_ini_path(config_path)
            self.logger.debug("Config sections: {0}".format(config.sections()))
        except ConfigParserError as err:
            msg = "Error of type {0} reading config file {1}: {2}".format(
                type(err).__name__,
                config_path,
                err
            )
            self.logger.error(msg)
            raise
        plugin_name = None
        for section_name in config.sections():
            if section_name == ini.CORE:
                continue
            elif plugin_name_supplied:
                if section_name == plugin_name_supplied:
                    plugin_name = section_name
            else:
                if plugin_name == None:
                    plugin_name = section_name
                else:
                    msg = "Cannot resolve multiple plugin names in {0}".format(config_path)
                    self.logger.error(msg)
                    raise RuntimeError(msg)
        if plugin_name == None:
            if plugin_name_supplied:
                msg = "Plugin name {0} not found in {1}".format(
                    plugin_name_supplied,
                    config_path
                )
            else:
                msg = "No plugin names found in {0}".format(config_path)
                self.logger.error(msg)
                raise RuntimeError(msg)
        plugin = self.plugin_loader.load(plugin_name)
        self.logger.info("Plugin {0} is OK!".format(plugin_name))
        return True


import sys # for 'main' method below

if __name__ == '__main__':
    tester = plugin_tester(log_level=logging.DEBUG)
    plugin_ok = tester.run(sys.argv[1], 'demo2')
