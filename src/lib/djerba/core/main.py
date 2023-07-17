"""
Main class to:
- Generate the core report elements
- Import and run plugins
- Merge and output results
"""
from configparser import ConfigParser
import csv
import json
import logging
import os
import re
import djerba.util.ini_fields as ini
import djerba.version as version
from djerba.core.base import base as core_base
from djerba.core.configure import configurer as core_configurer
from djerba.core.database.archiver import archiver
from djerba.core.extract import extractor as core_extractor
from djerba.core.json_validator import plugin_json_validator
from djerba.core.render import renderer as core_renderer
from djerba.core.loaders import \
    plugin_loader, merger_loader, helper_loader, core_config_loader
from djerba.core.workspace import workspace
from djerba.util.logger import logger
from djerba.util.validator import path_validator
import djerba.core.constants as cc
import djerba.util.constants as constants

class main(core_base):

    # TODO move to constants file(s)
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
        self.core_config_loader = core_config_loader(self.log_level, self.log_path)
        self.plugin_loader = plugin_loader(self.log_level, self.log_path)
        self.merger_loader = merger_loader(self.log_level, self.log_path)
        self.helper_loader = helper_loader(self.log_level, self.log_path)

    def _get_render_priority(self, plugin_data):
        return plugin_data[cc.PRIORITIES][cc.RENDER]

    def _load_component(self, name):
        if name == ini.CORE:
            component = self.core_config_loader.load()
        elif self._is_helper_name(name):
            component = self.helper_loader.load(name, self.workspace)
        elif self._is_merger_name(name):
            component = self.merger_loader.load(name)
        else:
            component = self.plugin_loader.load(name, self.workspace)
        return component

    def _parse_comma_separated_list(self, list_string):
        # parse INI values stored as a comma-separated list -- eg. attributes, dependencies
        # use CSV reader to allow escaping and handle other edge cases
        return next(csv.reader([list_string]))

    def _resolve_configure_dependencies(self, config, components, ordered_names):
        self._resolve_ini_deps(cc.DEPENDS_CONFIGURE, config, components, ordered_names)

    def _resolve_extract_dependencies(self, config, components, ordered_names):
        self._resolve_ini_deps(cc.DEPENDS_EXTRACT, config, components, ordered_names)

    def _resolve_ini_deps(self, depends_key, config, components, ordered_names):
        for name in ordered_names:
            if config.has_option(name, depends_key):
                depends_str = config.get(name, depends_key)
            else:
                depends_str = components[name].get_reserved_default(depends_key)
            depends = self._parse_comma_separated_list(depends_str)
            if len(depends)>0:
                failed = 0
                for dependency in depends:
                    dependency_ok = False
                    for other_name in ordered_names:
                        if other_name == name:
                            break
                        elif other_name == dependency:
                            dependency_ok = True
                            break
                    if not dependency_ok:
                        failed += 1
                if failed==0:
                    template = 'Resolved {0} dependencies for component {1}'
                    self.logger.debug(template.format(len(depends), name))
                else:
                    template = 'Failed to resolve {0} of {1} dependencies in {2} for '+\
                        'component {3}. One or more dependencies is missing or in the '+\
                        'wrong order. Dependencies: {4} Priority order: {5}'
                    args = [failed, len(depends), depends_key, name, depends, ordered_names]
                    msg = template.format(*args)
                    self.logger.error(msg)
                    raise DjerbaDependencyError(msg)
            else:
                self.logger.debug("No dependencies found for component {0}".format(name))

    def _run_merger(self, merger_name, data):
        """Assemble inputs for the named merger and run merge/dedup to get HTML"""
        merger_inputs = []
        total = 0
        for plugin_name in data[self.PLUGINS]:
            plugin_data = data[self.PLUGINS][plugin_name]
            if merger_name in plugin_data[self.MERGE_INPUTS]:
                merger_inputs.append(plugin_data[self.MERGE_INPUTS][merger_name])
                total += 1
        if total == 0:
            self.logger.warning("No inputs found for merger: {0}".format(merger_name))
        else:
            self.logger.debug("{0} inputs found for merger: {1}".format(total, merger_name))
        merger = self.merger_loader.load(merger_name)
        self.logger.debug("Loaded merger {0} for rendering".format(merger_name))
        return merger.render(merger_inputs)

    def configure(self, config_path_in, config_path_out=None):
        self.logger.info('Starting Djerba config step')
        if config_path_out:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_file(config_path_out)
        config_in = self.read_ini_path(config_path_in)
        components = {}
        priorities = {}
        # 1. Load components, set priorities, resolve dependencies (if any)
        self.logger.debug('Loading components and finding config priority levels')
        for section in config_in.sections():
            components[section] = self._load_component(section)
            # if input has a configure priority, use that
            # otherwise, use default priority for the component
            if config_in.has_option(section, cc.CONFIGURE_PRIORITY):
                priority = config_in.getint(section, cc.CONFIGURE_PRIORITY)
            else:
                priority = components[section].get_reserved_default(cc.CONFIGURE_PRIORITY)
            priorities[section] = priority
        self.logger.debug('Configuring components in priority order')
        ordered_names = sorted(priorities.keys(), key=lambda x: priorities[x])
        self._resolve_configure_dependencies(config_in, components, ordered_names)
        # 2. Validate and run configuration for each component; store in config_out
        config_out = ConfigParser()
        order = 0
        for name in ordered_names:
            order += 1
            component = components[name]
            priority = priorities[name]
            msg = 'Configuring {0}, priority {1}, order {2}'.format(name, priority, order)
            self.logger.debug(msg)
            component.validate_minimal_config(config_in)
            config_tmp = component.configure(config_in)
            component.validate_full_config(config_tmp)
            config_in[name] = config_tmp[name] # update config_in to support dependencies
            config_out[name] = config_tmp[name]
        if config_path_out:
            self.logger.debug('Writing INI output to {0}'.format(config_path_out))
            with open(config_path_out, 'w') as out_file:
                config_out.write(out_file)
        self.logger.info('Finished Djerba config step')
        return config_out

    def extract(self, config, json_path=None, archive=False):
        self.logger.info('Starting Djerba extract step')
        if json_path:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_file(json_path)
        components = {}
        priorities = {}
        # 1. Load components, set priorities, resolve dependencies (if any)
        for section in config.sections():
            if not (section == ini.CORE or self._is_merger_name(section)):
                components[section] = self._load_component(section)
                priorities[section] = config.getint(section, cc.EXTRACT_PRIORITY)
        self.logger.debug('Configuring components in priority order')
        ordered_names = sorted(priorities.keys(), key=lambda x: priorities[x])
        self._resolve_extract_dependencies(config, components, ordered_names)
        # 2. Validate and run configuration for each component; store in data structure
        self.logger.debug('Generating core data structure')
        data = core_extractor(self.log_level, self.log_path).run(config)
        self.logger.debug('Running extraction for plugins and mergers in priority order')
        order = 0
        for name in ordered_names:
            order += 1
            component = components[name]
            self.logger.debug('Extracting component {0} in order {1}'.format(name, order))
            component.validate_full_config(config)
            component_data = components[name].extract(config)
            if not self._is_helper_name(name):
                # only plugins, not helpers, write data in the JSON document
                self.json_validator.validate_data(component_data)
                data[self.PLUGINS][name] = component_data
        self.logger.debug('Finished running extraction')
        if json_path:
            self.logger.debug('Writing JSON output to {0}'.format(json_path))
            with open(json_path, 'w') as out_file:
                out_file.write(json.dumps(data))
        if archive:
            self.logger.info('Archiving not yet implemented for djerba.core')
            #uploaded, report_id = archiver(self.log_level, self.log_path).run(data)
            #if uploaded:
            #    self.logger.info(f"Archiving successful: {report_id}")
            #else:
            #    self.logger.warning(f"Error! Archiving unsuccessful: {report_id}")
        else:
            self.logger.info("Archive operation not requested; omitting archiving")
        self.logger.info('Finished Djerba extract step')
        return data

    def render(self, data, html_path=None):
        self.logger.info('Starting Djerba render step')
        if html_path:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_file(html_path)
        body = {} # HTML strings to make up the report body
        priorities = {}
        attributes = {}
        # 1. Load components, set priorities; dependencies are NOT defined for render
        self.logger.debug('Rendering plugin HTML')
        for plugin_name in data[self.PLUGINS]:
            # render plugin HTML, and find which mergers it uses
            plugin_data = data[self.PLUGINS][plugin_name]
            plugin = self.plugin_loader.load(plugin_name, self.workspace)
            body[plugin_name] = plugin.render(plugin_data)
            self.logger.debug("Ran plugin '{0}' for rendering".format(plugin_name))
            priorities[plugin_name] = self._get_render_priority(plugin_data)
            attributes[plugin_name] = plugin_data[cc.ATTRIBUTES]
        # 2. Validate and run rendering for each component; store in data structure
        for (merger_name, merger_config) in data[self.MERGERS].items():
            body[merger_name] = self._run_merger(merger_name, data)
            self.logger.debug("Ran merger '{0}' for rendering".format(merger_name))
            priorities[merger_name] = merger_config[cc.RENDER_PRIORITY]
            attributes[merger_name] = merger_config[cc.ATTRIBUTES]
        self.logger.debug("Assembling HTML document")
        renderer = core_renderer(self.log_level, self.log_path)
        html = renderer.run(body, priorities, attributes, data) # TODO remove data argument
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
        ap = arg_processor(args, self.logger, validate=False)
        mode = ap.get_mode()
        work_dir = ap.get_work_dir()
        if mode == constants.CONFIGURE:
            ini_path = ap.get_ini_path()
            ini_path_out = ap.get_ini_out_path() # may be None
            self.configure(ini_path, ini_path_out)
        elif mode == constants.EXTRACT:
            ini_path = ap.get_ini_path()
            json_path = ap.get_json_path()
            archive = ap.is_archive_enabled()
            config = self.read_ini_path(ini_path)
            self.extract(config, json_path, archive)
        elif mode == constants.HTML:
            json_path = ap.get_json_path()
            html_path = ap.get_html_path()
            with open(json_path) as json_file:
                data = json.loads(json_file.read())
            self.render(data, html_path)
        elif mode == constants.REPORT:
            # get operational parameters
            ini_path = ap.get_ini_path()
            ini_path_out = ap.get_ini_out_path() # may be None
            json_path = ap.get_json_path() # may be None
            html_path = ap.get_html_path()
            #pdf_path = ap.get_pdf()
            # caching and cleanup are plugin-specific, should be configured in INI
            # can also have a script to auto-populate INI files in 'setup' mode
            archive = ap.is_archive_enabled()
            config = self.configure(ini_path, ini_path_out)
            data = self.extract(config, json_path, archive)
            self.render(data, html_path)
            # TODO if pdf_path!=None, convert HTML->PDF
        else:
            # TODO add clauses for setup, pdf, etc.
            # for now, raise an error
            msg = "Mode '{0}' is not yet defined in Djerba core.main!".format(mode)
            self.logger.error(msg)
            raise RuntimeError(msg)

class arg_processor(logger):
    # class to process command-line args for creating a main object

    DEFAULT_JSON_FILENAME = 'djerba_report.json'

    def __init__(self, args, logger=None, validate=True):
        self.args = args
        if logger:
            # do not call 'get_logger' if one has already been configured
            # this way, we can preserve the level/path of an existing logger
            self.logger = logger
        else:
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
        json_arg = self._get_arg('json')
        if json_arg:
            json_path = json_arg
        else:
            work_dir = self.get_work_dir()
            if work_dir == None:
                msg = "Cannot find default JSON path, work_dir undefined"
                self.logger.error(msg)
                raise RuntimeError(msg)
            json_path = os.path.join(work_dir, self.DEFAULT_JSON_FILENAME)
        return json_path

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
        # use to auto-populate INI in 'setup' mode
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
            v.validate_output_file(args.ini_out)
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
                v.validate_output_file(args.html)
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

class DjerbaDependencyError(Exception):
    pass