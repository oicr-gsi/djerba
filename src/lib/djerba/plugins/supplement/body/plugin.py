"""Djerba plugin for supplementary report section"""

import json
import logging
import os
from djerba.plugins.base import plugin_base, DjerbaPluginError
import djerba.core.constants as core_constants
from djerba.util.date import get_todays_date
from djerba.util.date import is_valid_date
from djerba.util.render_mako import mako_renderer
import djerba.util.assays as assays

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 1200
    MAKO_TEMPLATE_NAME = 'supplementary_materials_template.html'
    TEMPLATE_DIR = "template_dir"
    PLUGIN_VERSION = '0.1'
    FAILED = "failed"
    ASSAY = "assay"
    COMPONENTS = 'components'
    REPORT_SIGNOFF_DATE = "report_signoff_date"
    USER_SUPPLIED_DRAFT_DATE = "user_supplied_draft_date"
    GENETICIST = "clinical_geneticist_name"
    GENETICIST_ID = "clinical_geneticist_licence"
    EXTRACT_DATE = "extract_date"
    INCLUDE_SIGNOFFS = "include_signoffs"
    GENETICIST_DEFAULT = 'PLACEHOLDER'
    GENETICIST_ID_DEFAULT = 'XXXXXXX'
    REPORT_SIGNOUT_DEFAULT = 'yyyy-mm-dd'

    # example URL for testing purposes, change to plugin repo when available
    URL = 'https://example.com/'

    def check_assay_name(self, wrapper):
        [ok, msg] = assays.name_status(wrapper.get_my_string(self.ASSAY))
        if not ok:
            self.logger.error(msg)
            raise DjerbaPluginError(msg)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        # Get input_data.json if it exists; else return None
        input_data = self.workspace.read_maybe_input_params()
        if wrapper.my_param_is_null(self.ASSAY):
            if input_data:
                wrapper.set_my_param(self.ASSAY, input_data[self.ASSAY])
            elif self.workspace.has_file("sample_info.json"):
                sample_info = self.workspace.read_json("sample_info.json")
                wrapper.set_my_param(self.ASSAY, sample_info[self.ASSAY])
            else: 
                msg = "Cannot find assay from input_params.json or manual config"
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        # If dates not supplied, set as today's date
        for param in [self.USER_SUPPLIED_DRAFT_DATE, self.REPORT_SIGNOFF_DATE]:
            if wrapper.my_param_is_null(param):
                wrapper.set_my_param(param, get_todays_date())
        self.check_assay_name(wrapper)

        # Check if custom template dir is supplied, if not default to module dir
        if wrapper.my_param_is_null(self.TEMPLATE_DIR):
            wrapper.set_my_param(self.TEMPLATE_DIR, self.get_module_dir())

        # Check if dates are valid
        user_supplied_date = wrapper.get_my_string(self.USER_SUPPLIED_DRAFT_DATE)
        report_signoff_date = wrapper.get_my_string(self.REPORT_SIGNOFF_DATE)
        dates_to_check = [user_supplied_date, ]
        if report_signoff_date != self.REPORT_SIGNOUT_DEFAULT:
            dates_to_check.append(report_signoff_date)
        for date in dates_to_check:
            if not is_valid_date(date):
                msg = "Invalid requisition approved date '{0}': ".format(date)+\
                      "Must be in yyyy-mm-dd format"
                self.logger.error(msg)
                raise ValueError(msg)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        draft_date = wrapper.get_my_string(self.USER_SUPPLIED_DRAFT_DATE)
        report_signoff_date = wrapper.get_my_string(self.REPORT_SIGNOFF_DATE)
        self.check_assay_name(wrapper)
        attributes_list = wrapper.get_my_attributes()
        if "clinical" in attributes_list:
            include_signoffs = True
        elif "research" in attributes_list:
            include_signoffs = False
        else:
            include_signoffs = False
            msg = "Excluding sign-offs for non-clinical attribute: {0}".format(attributes_list)
            self.logger.warning(msg)
        # read component version JSON written by core
        with self.workspace.open_file(core_constants.COMPONENT_FILENAME) as component_file:
            component_info = json.loads(component_file.read())
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {},
            'results': {
                self.ASSAY: wrapper.get_my_string(self.ASSAY),
                self.COMPONENTS: component_info,
                self.FAILED: wrapper.get_my_boolean(self.FAILED),
                core_constants.AUTHOR: config['core'][core_constants.AUTHOR],
                self.EXTRACT_DATE: draft_date,
                self.INCLUDE_SIGNOFFS: include_signoffs,
                self.TEMPLATE_DIR: wrapper.get_my_string(self.TEMPLATE_DIR)
            },
            core_constants.URL_KEY: self.URL,
            'version': self.PLUGIN_VERSION,
        }
        if include_signoffs:
            data['results'].update({
                self.REPORT_SIGNOFF_DATE: report_signoff_date,
                self.GENETICIST: wrapper.get_my_string(self.GENETICIST),
                self.GENETICIST_ID: wrapper.get_my_string(self.GENETICIST_ID)
            })
        return data

    def render(self, data):
        template_dir = data[core_constants.RESULTS][self.TEMPLATE_DIR]
        renderer = mako_renderer(template_dir)
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

    def specify_params(self):
        discovered = [
            self.ASSAY
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(self.REPORT_SIGNOFF_DATE, self.REPORT_SIGNOUT_DEFAULT)
        self.set_ini_default(self.USER_SUPPLIED_DRAFT_DATE, get_todays_date())
        self.set_ini_default(self.GENETICIST, self.GENETICIST_DEFAULT)
        self.set_ini_default(self.GENETICIST_ID, self.GENETICIST_ID_DEFAULT)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(self.FAILED, "False")
        self.set_ini_default(self.TEMPLATE_DIR, self.get_module_dir())
        self.set_priority_defaults(self.DEFAULT_CONFIG_PRIORITY)
