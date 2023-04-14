"""
Main class to:
- Generate the core report elements
- Import and run plugins
- Merge and output results
"""
from configparser import ConfigParser
import json
import logging
import os
import djerba.util.ini_fields as ini
import djerba.version as version
from djerba.core.configure import configurer as core_configurer
from djerba.core.extract import extractor as core_extractor
from djerba.core.json_validator import plugin_json_validator
from djerba.core.render import renderer as core_renderer
from djerba.core.loaders import plugin_loader, merger_loader
from djerba.core.workspace import workspace
from djerba.util.logger import logger
from djerba.util.validator import path_validator
import djerba.util.constants as constants

class main(logger):

    # TODO move to constants file(s)
    COMPONENT_ORDER = 'component_order'
    PLUGINS = 'plugins'
    MERGERS = 'mergers'
    MERGE_INPUTS = 'merge_inputs'
    
    def __init__(self, work_dir=None, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Running Djerba version {0}".format(version.__version__))
        self.json_validator = plugin_json_validator(self.log_level, self.log_path)
        self.path_validator = path_validator(self.log_level, self.log_path)
        self.work_dir = work_dir
        if self.work_dir != None:
            self.workspace = workspace(work_dir, self.log_level, self.log_path)
        else:
            self.workspace = None # eg. no workspace needed for 'render' only
        self.plugin_loader = plugin_loader(self.log_level, self.log_path)
        self.merger_loader = merger_loader(self.log_level, self.log_path)

    def _order_html(self, header, body, footer, order):
        """
        'body' is a dictionary of strings for the body of the HTML document
        'order' is a list of component names (must include all components in data)
        """
        ordered_html = [header, ]
        if len(order)==0:
            msg = "Component order is empty, falling back to default order"
            self.logger.info(msg)
            ordered_html.extend(body.values())
        else:
            for name in order:
                # refer to merger/plugin list in core data and assemble outputs
                if name not in body:
                    msg = "Name {0} not found ".format(name)+\
                        "in user-specified component order {0}".format(order)
                    self.logger.error(msg)
                    raise ComponentNameError(msg)
                ordered_html.append(body[name])
        ordered_html.append(footer)
        return ordered_html

    def _run_merger(self, merger_name, data):
        """Assemble inputs for the named merger and run merge/dedup to get HTML"""
        merger_inputs = []
        for plugin_name in data[self.PLUGINS]:
            plugin_data = data[self.PLUGINS][plugin_name]
            if merger_name in plugin_data[self.MERGE_INPUTS]:
                merger_inputs.append(plugin_data[self.MERGE_INPUTS][merger_name])
        merger = self.merger_loader.load(merger_name)
        self.logger.debug("Loaded merger {0} for rendering".format(merger_name))
        return merger.render(merger_inputs)

    def configure(self, config_path_in, config_path_out=None):
        self.logger.info('Starting Djerba config step')
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
                plugin_main = self.plugin_loader.load(section_name, self.workspace)
                self.logger.debug("Loaded plugin {0} for configuration".format(section_name))
                config_out[section_name] = plugin_main.configure(config_in[section_name])
        if config_path_out:
            with open(config_path_out, 'w') as out_file:
                config_out.write(out_file)
        self.logger.info('Finished Djerba config step')
        return config_out

    def extract(self, config, json_path=None):
        self.logger.info('Starting Djerba extract step')
        if json_path:  # do this *before* taking the time to generate output
            self.validator.validate_output_file(json_path)
        data = core_extractor(self.log_level, self.log_path).run(config)
        # data includes an empty 'plugins' object
        for section_name in config.sections():
            if section_name != ini.CORE:
                plugin = self.plugin_loader.load(section_name, self.workspace)
                self.logger.debug("Loaded plugin {0} for extraction".format(section_name))
                plugin_data = plugin.extract(config[section_name])
                self.json_validator.validate_data(plugin_data)
                data[self.PLUGINS][section_name] = plugin_data
        if json_path:
            with open(json_path, 'w') as out_file:
                out_file.write(json.dumps(data))
        self.logger.info('Finished Djerba extract step')
        return data

    def render(self, data, html_path=None):
        self.logger.info('Starting Djerba render step')
        if html_path:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_file(html_path)
        [header, footer] = core_renderer(self.log_level, self.log_path).run(data)
        body = {} # strings to make up the body of the HTML document
        merger_names = set()
        for plugin_name in data[self.PLUGINS]:
            # render plugin HTML, and find which mergers it uses
            plugin_data = data[self.PLUGINS][plugin_name]
            plugin = self.plugin_loader.load(plugin_name, self.workspace)
            self.logger.debug("Loaded plugin {0} for rendering".format(plugin_name))
            body[plugin_name] = plugin.render(plugin_data)
            for name in plugin_data[self.MERGE_INPUTS]:
                merger_names.add(name)
        for merger_name in merger_names:
            if merger_name in body:
                msg = "Plugin/merger name conflict: {0}".format(name)
                self.logger.error(msg)
                raise ComponentNameError(msg)
            merged_html = self._run_merger(merger_name, data)
            body[merger_name] = merged_html
        order = data[ini.CORE][self.COMPONENT_ORDER]
        ordered_html = self._order_html(header, body, footer, order)
        html = "\n".join(ordered_html)
        if html_path:
            with open(html_path, 'w') as out_file:
                out_file.write(html)
            self.logger.info("Wrote HTML output to {0}".format(html_path))
        self.logger.info('Finished Djerba render step')
        return html

    def read_ini_path(self, ini_path):
        self.path_validator.validate_input_file(ini_path)
        config = ConfigParser()
        config.read(ini_path)
        return config

    def run(self, args):
        # run from command-line args
        # path validation was done in command-line script
        ap = arg_processor(args, validate=False)
        mode = ap.get_mode()
        if mode == constants.REPORT:
            # get operational parameters
            work_dir = ap.get_work_dir()
            ini_path = ap.get_ini_path()
            ini_path_out = ap.get_ini_out_path()
            json_path = ap.get_json_path()
            html_path = ap.get_html_path()
            #pdf_path = ap.get_pdf()
            # TODO define archive/cleanup switches for extract
            # TODO apply/update cache switch for extract
            #archive = ap.is_archive_enabled()
            #cleanup = ap.is_cleanup_enabled()
            config = self.configure(ini_path, ini_path_out)
            data = self.extract(config, json_path)
            self.render(data, html_path)
            # TODO if pdf_path!=None, convert HTML->PDF
        else:
            # TODO add clauses for setup, configure, etc.
            # for now, raise an error
            msg = "Mode '{0}' is not defined in Djerba core.main!".format(mode)
            self.logger.error(msg)
            raise RuntimeError(msg)

class arg_processor(logger):
    # class to process command-line args for creating a main object

    def __init__(self, args, validate=True):
        self.args = args
        self.log_level = self.get_args_log_level(self.args)
        self.log_path = self.args.log_path
        if self.log_path:
            # we are verifying the log path, so don't write output there yet
            path_validator(self.log_level).validate_output_file(self.log_path)
        self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        if validate:
            self.validate_args(self.args)  # checks subparser and args are valid
        self.mode = self.args.subparser_name

    def _get_arg(self, arg_name):
        try:
            value = getattr(self.args, arg_name)
        except AttributeError as err:
            msg = "Argument {0} not defined in Djerba mode {1}".format(arg_name, self.mode)
            self.logger.error(msg)
            raise ArgumentNameError(msg) from err
        return value

    def get_ini_path(self):
        return self._get_arg('ini')

    def get_ini_out_path(self):
        return self._get_arg('ini_out')

    def get_json_path(self):
        return self._get_arg('json')
    
    def get_log_level(self):
        return self.log_level

    def get_log_path(self):
        return self.log_path

    def get_html_path(self):
        if hasattr(self.args, 'html') and self._get_arg('html') != None:
           value = self._get_arg('html')
        else:
            work_dir = self.get_work_dir()
            if work_dir == None:
                msg = "Cannot find default HTML path, work_dir undefined"
                self.logger.error(msg)
                raise RuntimeError(msg)
            value = os.path.join(work_dir, 'djerba_report.html')
        return value

    def get_mode(self):
        return self.mode

    def get_pdf_path(self):
        return self._get_arg('pdf')
    
    def get_work_dir(self):
        # default to None if work_dir is not in args
        # appropriate if eg. only running the 'render' step
        if hasattr(self.args, 'work_dir'):
           value = self._get_arg('work_dir')
        else:
            value = None
        return value

    def is_archive_enabled(self):
        return not self._get_arg('no_archive')

    def is_cleanup_enabled(self):
        return not self._get_arg('no_cleanup')
    
    def validate_args(self, args):
        """
        Check we can read/write paths in command-line arguments
        Assume logging has been initialized and log path (if any) is valid
        """
        self.logger.info("Validating paths in command-line arguments")
        v = path_validator(self.log_level, self.log_path)
        if args.subparser_name == constants.SETUP:
            v.validate_output_dir(args.base)
        elif args.subparser_name == constants.CONFIGURE:
            v.validate_input_file(args.ini)
            v.validate_output_file(args.out)
            v.validate_output_dir(args.work_dir)
        elif args.subparser_name == constants.EXTRACT:
            v.validate_input_file(args.ini)
            v.validate_output_dir(args.work_dir)
            if args.json:
                v.validate_output_file(args.json)
        elif args.subparser_name == constants.HTML:
            v.validate_input_file(args.json)
            v.validate_output_file(args.html)
            if args.pdf:
                v.validate_output_file(args.pdf)
        elif args.subparser_name == constants.PDF:
            v.validate_input_file(args.json)
            v.validate_output_dir(args.pdf)
        elif args.subparser_name == constants.REPORT:
            v.validate_input_file(args.ini)
            v.validate_output_dir(args.work_dir)
            if args.ini_out:
                v.validate_output_file(args.ini_out)
            if args.html:
                v.validate_output_file(args.pdf)
            if args.json:
                v.validate_output_file(args.json)
            if args.pdf:
                v.validate_output_file(args.pdf)
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: " + args.subparser_name)
        self.logger.info("Command-line path validation finished.")

class ArgumentNameError(Exception):
    pass

class ComponentNameError(Exception):
    pass
