"""
Main class to:
- Generate the core report elements
- Import and run plugins
- Merge and output results
"""
from configparser import ConfigParser
import logging
import json
import djerba.util.ini_fields as ini
from djerba.core.configure import configurer as core_configurer
from djerba.core.extract import extractor as core_extractor
from djerba.core.json_validator import plugin_json_validator
from djerba.core.render import renderer as core_renderer
from djerba.core.loaders import plugin_loader
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class main(logger):

    # TODO move to a constants file
    PLUGINS = 'plugins'
    MERGERS = 'mergers'
    
    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.json_validator = plugin_json_validator(self.log_level, self.log_path)
        self.path_validator = path_validator(self.log_level, self.log_path)
        self.plugin_loader = plugin_loader(self.log_level, self.log_path)

    def configure(self, config_path_in, config_path_out=None):
        if config_path_out:  # do this *before* taking the time to generate output
            self.validator.validate_output_file(config_path_out)
        config_in = self.read_ini_path(config_path_in)
        # TODO first read defaults, then overwrite
        config_out = ConfigParser()
        for section_name in config_in.sections():
            if section_name == ini.CORE:
                configurer = core_configurer(self.log_level, self.log_path)
                config_out[section_name] = configurer.run(config_in[section_name])
                self.logger.debug("Updated core configuration")
            else:
                plugin_main = self.plugin_loader.load(section_name)
                self.logger.debug("Loaded plugin {0} for configuration".format(section_name))
                config_out[section_name] = plugin_main.configure(config_in[section_name])
        if config_path_out:
            with open(config_path_out, 'w') as out_file:
                config_out.write(out_file)
        return config_out

    def extract(self, config, json_path=None):
        if json_path:  # do this *before* taking the time to generate output
            self.validator.validate_output_file(json_path)
        data = core_extractor(self.log_level, self.log_path).run(config)
        # data includes an empty 'plugins' object
        for section_name in config.sections():
            if section_name != ini.CORE:
                plugin = self.plugin_loader.load(section_name)
                self.logger.debug("Loaded plugin {0} for extraction".format(section_name))
                plugin_data = plugin.extract(config[section_name])
                self.json_validator.validate_data(plugin_data)
                data[self.PLUGINS][section_name] = plugin_data
        if json_path:
            with open(json_path, 'w') as out_file:
                out_file.write(json.dumps(data))
        return data

    def render(self, data, html_path=None):
        if html_path:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_file(html_path)
        [header, footer] = core_renderer(self.log_level, self.log_path).run(data)
        ordered_html = [header]
        # TODO control the order of plugin outputs
        # TODO merge/dedup for multi-plugin outputs
        # See 'shared element representation' in 'Report specs' google doc
        unordered_html = {}
        merger_names = set()
        for plugin_name in data[self.PLUGINS]:
            plugin_data = data[self.PLUGINS][plugin_name]
            plugin = self.plugin_loader.load(plugin_name)
            self.logger.debug("Loaded plugin {0} for rendering".format(plugin_name))
            unordered_html[plugin_name] = plugin.render(plugin_data)
            for name in plugin_data[self.MERGE_INPUTS]:
                merger_names.add(name)
        for merger_name in merger_names:
            if merger_name in unordered_html:
                msg = "Plugin/merger name conflict"
                self.logger.error(msg)
                raise RuntimeError(msg)
            merger = self.merger_loader.load(merger_name)
            self.logger.debug("Loaded merger {0} for rendering".format(merger_name))
            merger_inputs = []
            for plugin_name in data[self.PLUGINS]:
                plugin_data = data[self.PLUGINS][plugin_name]
                if merger_name in plugin_data[self.MERGER_INPUTS]:
                    merger_inputs.append(plugin_data[self.MERGER_INPUTS][merger_name])
            unordered_html[merger_name] = merger.render(merger_inputs)
        for name in data[self.COMPONENT_ORDER]: # merger/plugin list in core data
            if name not in unordered_html:
                msg = "Name {0} not found".format(name)
                self.logger.error(msg)
                raise RuntimeError(msg)
            ordered_html.append(unordered_html[name])
        ordered_html.append(footer)
        html = "\n".join(ordered_html)
        if html_path:
            with open(html_path, 'w') as out_file:
                out_file.write(html)
        return html

    def read_ini_path(self, ini_path):
        self.path_validator.validate_input_file(ini_path)
        config = ConfigParser()
        config.read(ini_path)
        return config

    # TODO write a run() method to:
    # - convert command-line args to appropriate inputs
    # - run configure/extract/render as required
    # - Do PDF conversion
    def run(self, args):
        pass

import sys

if __name__ == '__main__':
    djerba_main = main(logging.DEBUG)
    config = djerba_main.configure(sys.argv[1])
    data = djerba_main.extract(config)
    with open(sys.argv[2], 'w') as out_file:
        out_file.write(json.dumps(data, indent=4, sort_keys=True))
    html = djerba_main.render(data)
    print(html)
