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
from glob import glob
from PyPDF2 import PdfMerger
import djerba.util.ini_fields as ini
from djerba.core.base import base as core_base
from djerba.core.database import database
from djerba.util.date import get_todays_date
from djerba.core.extract import extraction_setup
from djerba.core.html_cache import html_cache, DjerbaHtmlCacheError
from djerba.core.ini_generator import ini_generator
from djerba.core.json_validator import plugin_json_validator
from djerba.core.render import html_renderer, pdf_renderer
from djerba.core.loaders import \
    plugin_loader, merger_loader, helper_loader, core_config_loader
from djerba.core.workspace import workspace
from djerba.util.args import arg_processor_base
from djerba.util.logger import logger
from djerba.util.validator import path_validator
from djerba.version import get_djerba_version
import djerba.core.constants as cc
import djerba.util.constants as constants

class main_base(core_base):

    """Base class with shared methods between core-main and mini-main"""

    PLUGINS = 'plugins'
    MERGERS = 'mergers'
    MERGE_INPUTS = 'merge_inputs'

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Running Djerba version {0}".format(get_djerba_version()))
        self.work_dir = work_dir
        # make some utility objects
        self.json_validator = plugin_json_validator(self.log_level, self.log_path)
        self.path_validator = path_validator(self.log_level, self.log_path)
        self.html_cache = html_cache(self.log_level, self.log_path)
        # create a workspace in case it's needed (may not be for some modes/plugins)
        self.workspace = workspace(work_dir, self.log_level, self.log_path)
        self.core_config_loader = core_config_loader(self.log_level, self.log_path)
        self.plugin_loader = plugin_loader(self.log_level, self.log_path)
        self.merger_loader = merger_loader(self.log_level, self.log_path)
        self.helper_loader = helper_loader(self.log_level, self.log_path)

    def _get_render_priority(self, plugin_data):
        return plugin_data[cc.PRIORITIES][cc.RENDER]

    def _get_unique_doc_key(self, data):
        """
        Get the unique document key used to index the HTML cache
        Raise an error unless exactly 1 key is found
        For now, we only support update mode when report has exactly 1 document type
        """
        self._validate_html_cache_input(data)
        if len(data[cc.HTML_CACHE])==1:
            key = list(data[cc.HTML_CACHE].keys())[0]
        else:
            msg = "HTML cache update requries exactly 1 report type; "+\
                "found {0}".format(data[cc.HTML_CACHE].keys())
            self.logger.error(msg)
            raise DjerbaUpdateKeyError(msg)
        return key

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

    def _validate_html_cache_input(self, data):
        if not cc.HTML_CACHE in data:
            self.logger.debug("HTML cache not found in input JSON!")
            version = data[cc.CORE][cc.CORE_VERSION]
            msg = "Djerba core version error; input JSON is version {0}, ".format(version)+\
                "mini-djerba requires version 1.7.0 or higher"
            self.logger.error(msg)
            raise DjerbaVersionMismatchError(msg)

    def base_extract(self, config):
        """
        Base extract operation, shared between core and mini Djerba
        Just get the data structure; no additional write/archive actions
        """
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
                # only plugins and mergers, not helpers, write data in the JSON document
                self.json_validator.validate_data(component_data)
                data[self.PLUGINS][name] = component_data
        # 3. Render the HTML; encode and store in data structure
        self.logger.debug('Generating HTML for cache')
        data[cc.HTML_CACHE] = {}
        rendered = self.base_render(data)
        for prefix in rendered[cc.DOCUMENTS].keys():
            # cache HTML for each report type -- clinical, research, etc.
            encoded = self.html_cache.encode_to_base64(rendered[cc.DOCUMENTS][prefix])
            data[cc.HTML_CACHE][prefix] = encoded
        self.logger.debug('Finished running extraction')
        return data

    def base_render(self, data, out_dir=None, pdf=False):
        """
        Base render operation, shared between core and mini Djerba
        Write the HTML and (optional) PDF; no archiving
        """
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
            html_raw = plugin.render(plugin_data)
            html[plugin_name] = self.html_cache.wrap_html(plugin_name, html_raw)
            self.logger.debug("Ran plugin '{0}' for rendering".format(plugin_name))
            priorities[plugin_name] = self._get_render_priority(plugin_data)
            attributes[plugin_name] = plugin_data[cc.ATTRIBUTES]
        for (merger_name, merger_config) in data[self.MERGERS].items():
            html_raw = self._run_merger(merger_name, data)
            html[merger_name] = self.html_cache.wrap_html(merger_name, html_raw)
            self.logger.debug("Ran merger '{0}' for rendering".format(merger_name))
            priorities[merger_name] = merger_config[cc.RENDER_PRIORITY]
            attributes[merger_name] = merger_config[cc.ATTRIBUTES]
        # 2. Assemble plugin/merger HTML outputs according to their priorities/attributes
        self.logger.debug("Assembling HTML document(s)")
        h_rend = html_renderer(data[cc.CORE], self.log_level, self.log_path)
        output_data = h_rend.run(html, priorities, attributes)
        # 3. Write output files, if any
        if out_dir:
            p_rend = pdf_renderer(self.log_level, self.log_path)
            for prefix in output_data[cc.DOCUMENTS].keys():
                html_path = os.path.join(out_dir, prefix+'.html')
                with open(html_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
                    out_file.write(output_data[cc.DOCUMENTS][prefix])
                self.logger.info("Wrote HTML output to {0}".format(html_path))
                if pdf:
                    pdf_path = os.path.join(out_dir, prefix+'.pdf')
                    footer = output_data[cc.PDF_FOOTERS][prefix]
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

    def configure_from_parser(self, config_in, config_path_out=None):
        """
        Run the Djerba configure step, with a ConfigParser as input
        In update mode, we generate the ConfigParser on-the-fly instead of reading a file
        """
        self.logger.info('Starting Djerba config step')
        if config_path_out:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_file(config_path_out)
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
            with open(config_path_out, 'w', encoding=cc.TEXT_ENCODING) as out_file:
                config_out.write(out_file)
        self.logger.info('Finished Djerba config step')
        return config_out

    def render_from_cache(self, extracted_data, doc_key, out_dir, pdf):
        """
        Write HTML and (if required) PDF from the JSON HTML cache for the given doc key
        """
        self._validate_html_cache_input(extracted_data)
        html_str = self.html_cache.decode_from_base64(extracted_data[cc.HTML_CACHE][doc_key])
        html_path = os.path.join(out_dir, doc_key+'.html')
        with open(html_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
            out_file.write(html_str)
        if pdf:
            report_id = extracted_data[cc.CORE][cc.REPORT_ID]
            # PDF footer here duplicates the clinical report footer format
            # TODO support other footer types when rendering from cache
            footer = "{0} - {1}".format(get_todays_date(), report_id)
            p_rend = pdf_renderer(self.log_level, self.log_path)
            pdf_path = os.path.join(out_dir, doc_key+'.pdf')
            p_rend.render_file(html_path, pdf_path, footer)
            self.logger.info("Wrote PDF output to {0}".format(pdf_path))

    def update_report_data(self, new_data, data, force):
        """Apply updates and return the updated report data structure"""
        # new data overwrites old, on a per-plugin basis
        # ie. overwriting a given plugin is all-or-nothing
        # also overwrite JSON config section for the plugin
        # if plugin data did not exist in old JSON, it will be added
        # check plugin version numbers in old/new JSON
        # This updates plugins only; core data (including report timestamp) is not altered
        self._validate_html_cache_input(data)
        new_html = {}
        for plugin_name in new_data[self.PLUGINS].keys():
            old_version = data[self.PLUGINS][plugin_name][cc.VERSION]
            new_version = new_data[self.PLUGINS][plugin_name][cc.VERSION]
            if old_version != new_version:
                msg = "Versions differ for {0} plugin: ".format(plugin_name)+\
                    "Old version = {0}, new version = {1}".format(old_version, new_version)
                if force:
                    msg += "; --force option in effect, proceeding"
                    self.logger.warning(msg)
                else:
                    msg += "; run with --force to proceed"
                    self.logger.error(msg)
                    raise DjerbaVersionMismatchError(msg)
            data[self.PLUGINS][plugin_name] = new_data[self.PLUGINS][plugin_name]
            data[constants.CONFIG][plugin_name] = new_data[constants.CONFIG][plugin_name]
            # load the plugin and render HTML for cache update
            plugin = self.plugin_loader.load(plugin_name, self.workspace)
            raw_html = plugin.render(new_data[self.PLUGINS][plugin_name])
            new_html[plugin_name] = self.html_cache.wrap_html(plugin_name, raw_html)
            self.logger.debug('Updated JSON for plugin {0}'.format(plugin_name))
        # now update the HTML cache; TODO support multiple doc types, eg. clinical/research
        doc_key = self._get_unique_doc_key(data)
        old_cache = data[cc.HTML_CACHE][doc_key]
        new_html_string = self.html_cache.update_cached_html(new_html, old_cache)
        new_cache = self.html_cache.encode_to_base64(new_html_string)
        data[cc.HTML_CACHE][doc_key] = new_cache
        self.logger.debug('Updated HTML cache for all plugins')
        return data

    def update_data_from_file(self, new_data, json_path, force):
        """Read old JSON from a file, and return the updated data structure"""
        with open(json_path, encoding=cc.TEXT_ENCODING) as in_file:
            data = json.loads(in_file.read())
        return self.update_report_data(new_data, data, force)


class main(main_base):

    """Main class for Djerba core"""

    def configure(self, config_path_in, config_path_out=None):
        """
        Run the Djerba configure step, with an INI path as input
        """
        self.logger.info('Reading INI config file "{0}"'.format(config_path_in))
        config_in = self.read_ini_path(config_path_in)
        return self.configure_from_parser(config_in, config_path_out)

    def extract(self, config, json_path=None, archive=False):
        self.logger.info('Starting Djerba extract step')
        if json_path:  # do this *before* taking the time to generate output
            self.path_validator.validate_output_file(json_path)
        data = self.base_extract(config)
        if not json_path:
            json_path = self.get_default_json_output_path(data)
        self.logger.debug('Writing JSON output to {0}'.format(json_path))
        with open(json_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
            out_file.write(json.dumps(data))
        if archive:
            self.upload_archive(data)
        else:
            self.logger.info("Omitting archive upload at extract step")
        self.logger.info('Finished Djerba extract step')
        return data

    def get_json_input_path(self, json_arg):
        if json_arg:
            input_path = json_arg
        else:
            candidates = glob(os.path.join(self.work_dir, '*'+cc.REPORT_JSON_SUFFIX))
            total = len(candidates)
            if total == 0:
                msg = 'Cannot find default JSON path; work_dir has no files '+\
                    'ending in "{0}"'+format(cc.REPORT_JSON_SUFFIX)
                self.logger.error(msg)
                raise RuntimeError(msg)
            elif total > 1:
                msg = 'Cannot find default JSON path; multiple candidates '+\
                    'ending in "{0}": {1}'+format((cc.REPORT_JSON_SUFFIX, candidates))
                self.logger.error(msg)
                raise RuntimeError(msg)
            else:
                input_path = candidates[0]
        return input_path

    def get_default_json_output_path(self, data):
        filename = data[cc.CORE][cc.REPORT_ID]+cc.REPORT_JSON_SUFFIX
        json_path = os.path.join(self.work_dir, filename)
        return json_path

    def render(self, data, out_dir=None, pdf=False, archive=False):
        self.logger.info('Starting Djerba render step')
        # Archive the JSON data structure, if needed
        if archive:
            self.upload_archive(data)
        else:
            self.logger.debug("Omitting archive upload at render step")
        # run the main rendering operation
        return self.base_render(data, out_dir, pdf)

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
            json_arg = ap.get_json()
            archive = ap.is_archive_enabled()
            config = self.read_ini_path(ini_path)
            self.extract(config, json_arg, archive)
        elif mode == constants.RENDER:
            json_path = self.get_json_input_path(ap.get_json())
            archive = ap.is_archive_enabled()
            with open(json_path) as json_file:
                data = json.loads(json_file.read())
            self.render(data, ap.get_out_dir(), ap.is_pdf_enabled(), archive)
        elif mode == constants.REPORT:
            ini_path = ap.get_ini_path()
            out_dir = ap.get_out_dir()
            ini_path_out = os.path.join(out_dir, 'full_config.ini')
            json_path = None # write JSON to default workspace location
            archive = ap.is_archive_enabled()
            config = self.configure(ini_path, ini_path_out)
            # upload to archive at the extract step, not the render step
            data = self.extract(config, json_path, archive)
            self.render(data, ap.get_out_dir(), ap.is_pdf_enabled(), archive=False)
        elif mode == constants.UPDATE:
            ini_path = ap.get_ini_path()
            if ini_path == None:
                config_path = ap.get_summary_path()
                summary_only = True
            else:
                config_path = ini_path
                summary_only = False
            jp = self.get_json_input_path(ap.get_json())
            out_dir = ap.get_out_dir()
            archive = ap.is_archive_enabled()
            pdf = ap.is_pdf_enabled()
            force = ap.is_forced()
            self.update(config_path, jp, out_dir, archive, pdf, summary_only, force)
        else:
            msg = "Mode '{0}' is not defined in Djerba core.main!".format(mode)
            self.logger.error(msg)
            raise RuntimeError(msg)

    def setup(self, assay, ini_path, compact):
        if assay == 'WGTS':
            component_list = [
                'core',
                'input_params_helper',
                'provenance_helper',
                'report_title',
                'patient_info',
                'case_overview',
                'treatment_options_merger',
                'summary',
                'sample',
                'genomic_landscape',
                'expression_helper',
                'wgts.snv_indel',
                'wgts.cnv_purple',
                'fusion',
                'gene_information_merger',
                'supplement.body',
            ]
        elif assay == 'WGS':
            component_list = [
                'core',
                'input_params_helper',
                'provenance_helper',
                'report_title',
                'patient_info',
                'case_overview',
                'treatment_options_merger',
                'summary',
                'sample',
                'genomic_landscape',
                'wgts.snv_indel',
                'wgts.cnv_purple',
                'gene_information_merger',
                'supplement.body',
            ]
        elif assay == 'TAR':
            component_list = [
                'core',
                'tar_input_params_helper',
                'provenance_helper',
                'report_title',
                'patient_info',
                'case_overview',
                'treatment_options_merger',
                'summary',
                'tar.sample',
                'tar.snv_indel',
                'tar.swgs',
                'gene_information_merger',
                'supplement.body',
            ]
        elif assay == 'PWGS':
            component_list = [
                'core',
                'report_title',
                'patient_info',
                'pwgs_provenance_helper',
                'pwgs_cardea_helper',
                'pwgs.case_overview',
                'pwgs.summary',
                'pwgs.sample',
                'pwgs.analysis',  
                'supplement.body'
            ]
        else:
            msg = "Invalid assay name '{0}'".format(assay)
            self.logger.error(msg)
            raise ValueError(msg)
        generator = ini_generator(self.log_level, self.log_path)
        generator.write_config(component_list, ini_path, compact)
        self.logger.info("Wrote config for {0} to {1}".format(assay, ini_path))

    def update(self, config_path, json_path, out_dir, archive, pdf, summary_only, force):
        # update procedure:
        # 1. run plugins from user-supplied config to get 'new' (updated) JSON
        # 2. update the 'old' (user-supplied) JSON
        # 3. optionally, upload the merged JSON to couchDB
        # 4. optionally, use the merged JSON to generate HTML/PDF
        #
        # Two ways to configure:
        # 1. INI config with core + plugins to update
        # 2. Text file to update summary only
        # The 'summary_only' argument controls which one is used
        if summary_only:
            # make an appropriate ConfigParser on-the-fly
            config_in = ConfigParser()
            config_in.add_section(cc.CORE)
            config_in.add_section('summary')
            config_in.set('summary', 'summary_file', config_path)
            config = self.configure_from_parser(config_in)
        else:
            config = self.configure(config_path)
        with open(json_path, encoding=cc.TEXT_ENCODING) as in_file:
            data = json.loads(in_file.read())
        data_new = self.base_extract(config)
        data = self.update_data_from_file(data_new, json_path, force)
        if archive:
            self.upload_archive(data)
        else:
            self.logger.info("Omitting archive upload for update")
        if out_dir:
            doc_key = self._get_unique_doc_key(data)
            self.render_from_cache(data, doc_key, out_dir, pdf)
            input_name = os.path.basename(json_path)
            # generate an appropriate output filename
            if re.search('\.updated\.json$', json_path):
                output_name = input_name
            elif not re.search('\.json$', json_path):
                output_name = input_name+'.updated.json'
            else:
                terms = re.split('\.', input_name)
                terms.pop()
                output_name = '.'.join(terms)+'.updated.json'
            json_path = os.path.join(out_dir, output_name)
            with open(json_path, 'w', encoding=cc.TEXT_ENCODING) as out_file:
                print(json.dumps(data), file=out_file)

    def upload_archive(self, data):
        for plugin_name in data[self.PLUGINS]:
            # load each plugin and redact PHI (if any)
            plugin_data = data[self.PLUGINS][plugin_name]
            plugin = self.plugin_loader.load(plugin_name, self.workspace)
            data[self.PLUGINS][plugin_name] = plugin.redact(plugin_data)
        uploaded, report_id = database(self.log_level, self.log_path).upload_data(data)
        if uploaded:
            self.logger.info(f"Archiving was successful: {report_id}")
        else:
            self.logger.warning(f"Archiving was NOT successful: {report_id}")


class arg_processor(arg_processor_base):
    # class to process command-line args for creating a main object

    def get_assay(self):
        return self._get_arg('assay')

    def get_compact(self):
        return self._get_arg('compact')

    def get_ini_path(self):
        return self._get_arg('ini')

    def get_ini_out_path(self):
        return self._get_arg('ini_out')

    def get_summary_path(self):
        return self._get_arg('summary')

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
        elif args.subparser_name == constants.UPDATE:
            if args.ini != None:
                v.validate_input_file(args.ini)
            else:
                v.validate_input_file(args.summary)
            v.validate_input_file(args.json)
            v.validate_output_dir(args.out_dir)
            if args.work_dir != None: # work_dir is optional in report mode
                v.validate_output_dir(args.work_dir)
        elif args.subparser_name == None:
            msg = "No subcommand name given; run with -h/--help for valid names"
            raise DjerbaSubcommandError(msg)
        else:
            # shouldn't happen, but handle this case for completeness
            raise DjerbaSubcommandError("Unknown subcommand: " + args.subparser_name)
        self.logger.info("Command-line path validation finished.")

class DjerbaDependencyError(Exception):
    pass

class DjerbaSubcommandError(Exception):
    pass

class DjerbaUpdateKeyError(Exception):
    pass

class DjerbaVersionMismatchError(Exception):
    pass
