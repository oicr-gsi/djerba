"""
Main class to:
- Generate the core report elements
- Import and run plugins
- Merge and output results
"""
from configparser import ConfigParser
import json
import logging
import pdfkit
import os
import re
from PyPDF2 import PdfMerger
import djerba.util.ini_fields as ini
import djerba.version as version
from djerba.core.base import base as core_base
from djerba.core.database import database
from djerba.core.extract import extraction_setup
from djerba.core.ini_generator import ini_generator
from djerba.core.json_validator import plugin_json_validator
from djerba.core.render import html_renderer, pdf_renderer
from djerba.core.loaders import \
    plugin_loader, merger_loader, helper_loader, core_config_loader
from djerba.core.workspace import workspace
from djerba.util.logger import logger
from djerba.util.validator import path_validator
import djerba.core.constants as cc
import djerba.util.constants as constants

class main(core_base):

    PLUGINS = 'plugins'
    MERGERS = 'mergers'
    MERGE_INPUTS = 'merge_inputs'

    def __init__(self, work_dir, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Running Djerba version {0}".format(version.__version__))
        self.json_validator = plugin_json_validator(self.log_level, self.log_path)
        self.path_validator = path_validator(self.log_level, self.log_path)
        self.work_dir = work_dir
        # create a workspace in case it's needed (may not be for some modes/plugins)
        self.workspace = workspace(work_dir, self.log_level, self.log_path)
        self.core_config_loader = core_config_loader(self.log_level, self.log_path)
        self.plugin_loader = plugin_loader(self.log_level, self.log_path)
        self.merger_loader = merger_loader(self.log_level, self.log_path)
        self.helper_loader = helper_loader(self.log_level, self.log_path)
    def _get_render_priority(self, plugin_data):
        return plugin_data[cc.PRIORITIES][cc.RENDER]

    def _load_component(self, name):
        if name == ini.CORE:
            component = self.core_config_loader.load(self.workspace)
        elif self._is_helper_name(name):
            component = self.helper_loader.load(name, self.workspace)
        elif self._is_merger_name(name):
            component = self.merger_loader.load(name)
        else:
            component = self.plugin_loader.load(name, self.workspace)
        return component

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
                    if self._is_merger_name(dependency):
                        msg = "Cannot specify dependency on merger '{0}'".format(dependency)
                        self.logger.error(msg)
                        raise DjerbaDependencyError(msg)
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
        data = extraction_setup(self.log_level, self.log_path).run(config)
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
            self.upload_archive(data)
        else:
            self.logger.info("Omitting archive upload at extract step")
        self.logger.info('Finished Djerba extract step')
        return data

    def render(self, data, out_dir=None, pdf=False, archive=False):
        self.logger.info('Starting Djerba render step')
        if out_dir:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_dir(out_dir)
        html = {} # HTML strings to make up the report file(s)
        priorities = {}
        attributes = {}
        # 1. Run plugins and mergers to render HTML
        self.logger.debug('Rendering plugin HTML')
        for plugin_name in data[self.PLUGINS]:
            plugin_data = data[self.PLUGINS][plugin_name]
            plugin = self.plugin_loader.load(plugin_name, self.workspace)
            html[plugin_name] = plugin.render(plugin_data)
            self.logger.debug("Ran plugin '{0}' for rendering".format(plugin_name))
            priorities[plugin_name] = self._get_render_priority(plugin_data)
            attributes[plugin_name] = plugin_data[cc.ATTRIBUTES]
        for (merger_name, merger_config) in data[self.MERGERS].items():
            html[merger_name] = self._run_merger(merger_name, data)
            self.logger.debug("Ran merger '{0}' for rendering".format(merger_name))
            priorities[merger_name] = merger_config[cc.RENDER_PRIORITY]
            attributes[merger_name] = merger_config[cc.ATTRIBUTES]
        # 2. Assemble plugin/merger HTML outputs according to their priorities/attributes
        self.logger.debug("Assembling HTML document(s)")
        h_rend = html_renderer(data[cc.CORE], self.log_level, self.log_path)
        output_data = h_rend.run(html, priorities, attributes)
        # 3. Archive the JSON data structure, if needed
        if archive:
            self.upload_archive(data)
        else:
            self.logger.debug("Omitting archive upload at render step")
        # 4. Write output files, if any
        if out_dir:
            p_rend = pdf_renderer(self.log_level, self.log_path)
            for prefix in output_data[cc.DOCUMENTS].keys():
                html_path = os.path.join(out_dir, prefix+'.html')
                with open(html_path, 'w') as out_file:
                    out_file.write(output_data[cc.DOCUMENTS][prefix])
                self.logger.info("Wrote HTML output to {0}".format(html_path))
                if pdf:
                    pdf_path = os.path.join(out_dir, prefix+'.pdf')
                    footer = output_data[cc.PAGE_FOOTER]
                    p_rend.render_file(html_path, pdf_path, footer)
                    self.logger.info("Wrote PDF output to {0}".format(pdf_path))
            merge_list = output_data[cc.MERGE_LIST]
            if pdf and len(merge_list)>1:
                merge_in = [os.path.join(out_dir, x+'.pdf') for x in merge_list]
                merge_out = os.path.join(out_dir, output_data[cc.MERGED_FILENAME])
                p_rend.merge_pdfs(merge_in, merge_out)
                self.logger.info("Wrote merged PDF output to {0}".format(merge_out))
        self.logger.info('Finished Djerba render step')
        return output_data

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
        if mode == constants.SETUP:
            assay = ap.get_assay()
            compact = ap.get_compact()
            ini_path = ap.get_ini_path()
            if ini_path == None:
                ini_path = os.path.join(os.getcwd(), 'config.ini')
            self.setup(assay, ini_path, compact)
        elif mode == constants.CONFIGURE:
            ini_path = ap.get_ini_path()
            ini_path_out = ap.get_ini_out_path() # may be None
            self.configure(ini_path, ini_path_out)
        elif mode == constants.EXTRACT:
            ini_path = ap.get_ini_path()
            json_path = ap.get_json_path()
            archive = ap.is_archive_enabled()
            config = self.read_ini_path(ini_path)
            self.extract(config, json_path, archive)
        elif mode == constants.RENDER:
            json_path = ap.get_json_path()
            archive = ap.is_archive_enabled()
            with open(json_path) as json_file:
                data = json.loads(json_file.read())
            self.render(data, ap.get_out_dir(), ap.is_pdf_enabled(), archive)
        elif mode == constants.REPORT:
            ini_path = ap.get_ini_path()
            out_dir = ap.get_out_dir()
            ini_path_out = os.path.join(out_dir, 'full_config.ini')
            json_path = os.path.join(out_dir, 'djerba_report.json')
            archive = ap.is_archive_enabled()
            config = self.configure(ini_path, ini_path_out)
            # upload to archive at the extract step, not the render step
            data = self.extract(config, json_path, archive)
            self.render(data, ap.get_out_dir(), ap.is_pdf_enabled(), archive=False)
        else:
            msg = "Mode '{0}' is not defined in Djerba core.main!".format(mode)
            self.logger.error(msg)
            raise RuntimeError(msg)

    def setup(self, assay, ini_path, compact):
        if assay == 'WGTS':
            component_list = [
                'core',
                'expression_helper',
                'input_params_helper',
                'provenance_helper',
                'gene_information_merger',
                'treatment_options_merger',
                'case_overview',
                'cnv',
                'fusion',
                'sample',
                'summary',
                'supplement.header',
                'supplement.body',
                'wgts.snv_indel'
            ]
        elif assay == 'WGS':
            component_list = [
                'core',
                'input_params_helper',
                'provenance_helper',
                'gene_information_merger',
                'treatment_options_merger',
                'case_overview',
                'cnv',
                'sample',
                'summary',
                'supplement.header',
                'supplement.body',
                'wgts.snv_indel'
             ]
	elif assay == 'TAR':
            component_list = [
                'core',
                'tar_input_params_helper',
                'provenance_helper',
                'gene_information_merger',
                'treatment_options_merger',
                'case_overview',
                'tar.sample',
                'tar.swgs', 
                'summary',
                'supplement.header',
                'supplement.body',
                'tar.snv_indel'
            ]
        elif assay == 'PWGS':
            component_list = [
                'core',
                'input_params_helper',
                'provenance_helper',
                'pwgs.sample',
                'pwgs.analysis',  
                'supplement.header',
                'supplement.body'
            ]
        else:
            msg = "Invalid assay name '{0}'".format(assay)
            self.logger.error(msg)
            raise ValueError(msg)
        generator = ini_generator(self.log_level, self.log_path)
        generator.write_config(component_list, ini_path, compact)
        self.logger.info("Wrote config for {0} to {1}".format(assay, ini_path))

    def upload_archive(self, data):
        uploaded, report_id = database(self.log_level, self.log_path).upload_data(data)
        if uploaded:
            self.logger.info(f"Archiving was successful: {report_id}")
        else:
            self.logger.warning(f"Archiving was NOT successful: {report_id}")


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

    def get_assay(self):
        return self._get_arg('assay')

    def get_compact(self):
        return self._get_arg('compact')

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

    def get_mode(self):
        return self.mode

    def get_out_dir(self):
        return self._get_arg('out_dir')

    def get_work_dir(self):
        if hasattr(self.args, 'work_dir'):
            # if work_dir is defined and non-empty, use it
            value = self._get_arg('work_dir')
            if value == None:
                # if work_dir is defined and empty, default to out_dir
                value = self._get_arg('out_dir')
        elif hasattr(self.args, 'out_dir'):
            # if work_dir is not defined, default to out_dir (eg. render mode)
            value = self._get_arg('out_dir')
        else:
            # if all else fails (eg. setup mode), use the current directory
            value = os.getcwd()
        return value

    def is_archive_enabled(self):
        return not self._get_arg('no_archive')

    def is_cleanup_enabled(self):
        # use to auto-populate INI in 'setup' mode
        return not self._get_arg('no_cleanup')

    def is_pdf_enabled(self):
        return self._get_arg('pdf')

    def validate_args(self, args):
        """
        Check we can read/write paths in command-line arguments
        Assume logging has been initialized and log path (if any) is valid
        """
        self.logger.info("Validating paths in command-line arguments")
        v = path_validator(self.log_level, self.log_path)
        if args.subparser_name == constants.SETUP:
            if args.ini!=None:
                v.validate_output_file(args.ini)
        elif args.subparser_name == constants.CONFIGURE:
            v.validate_input_file(args.ini)
            v.validate_output_file(args.ini_out)
            v.validate_output_dir(args.work_dir)
        elif args.subparser_name == constants.EXTRACT:
            v.validate_input_file(args.ini)
            v.validate_output_dir(args.work_dir)
            if args.json:
                v.validate_output_file(args.json)
        elif args.subparser_name == constants.RENDER:
            v.validate_input_file(args.json)
            v.validate_output_dir(args.out_dir)
        elif args.subparser_name == constants.REPORT:
            v.validate_input_file(args.ini)
            if args.work_dir != None: # work_dir is optional in report mode
                v.validate_output_dir(args.work_dir)
            v.validate_output_dir(args.out_dir)
        else:
            # shouldn't happen, but handle this case for completeness
            raise ValueError("Unknown subparser: " + args.subparser_name)
        self.logger.info("Command-line path validation finished.")

class ArgumentNameError(Exception):
    pass

class DjerbaDependencyError(Exception):
    pass
