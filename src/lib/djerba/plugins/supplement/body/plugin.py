"""Djerba plugin for pwgs supplement"""
import logging
import os
from djerba.plugins.base import plugin_base, DjerbaPluginError
import djerba.core.constants as core_constants
from djerba.util.render_mako import mako_renderer
import djerba.util.assays as assays
import djerba.util.input_params_tools as input_params_tools
from time import strftime

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 1200
    MAKO_TEMPLATE_NAME = 'supplementary_materials_template.html'
    SUPPLEMENT_DJERBA_VERSION = 0.1
    FAILED = "failed"
    ASSAY = "assay"
    REPORT_SIGNOFF_DATE = "report_signoff_date"
    USER_SUPPLIED_DRAFT_DATE = "user_supplied_draft_date"
    NONE_SPECIFIED = "NONE_SPECIFIED"
    GENETICIST = "clinical_geneticist_name"
    GENETICIST_ID = "clinical_geneticist_licence"
    EXTRACT_DATE = "extract_date"

    GENETICIST_DEFAULT = 'Trevor Pugh, PhD, FACMG'
    GENETICIST_ID_DEFAULT = '1027812'

    def check_assay_name(self, wrapper):
        [ok, msg] = assays.name_status(wrapper.get_my_string(self.ASSAY))
        if not ok:
            self.logger.error(msg)
            raise DjerbaPluginError(msg)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        # Get input_data.json if it exists; else return None
        input_data = input_params_tools.get_input_params_json(self)
        if input_data == None:
            msg = "File input_params.json does not exist. Parameters must be set manually."
            self.logger.info(msg)
        if wrapper.my_param_is_null(self.ASSAY):
            if input_data:
                wrapper.set_my_param(self.ASSAY, input_data[self.ASSAY])
            else:
                msg = "Cannot find assay from input_params.json or manual config"
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        if wrapper.my_param_is_null(self.USER_SUPPLIED_DRAFT_DATE):
            wrapper.set_my_param(self.USER_SUPPLIED_DRAFT_DATE, self.NONE_SPECIFIED)
        if wrapper.my_param_is_null(self.REPORT_SIGNOFF_DATE):
            wrapper.set_my_param(self.REPORT_SIGNOFF_DATE, self.NONE_SPECIFIED)
        self.check_assay_name(wrapper)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        if wrapper.get_my_string(self.USER_SUPPLIED_DRAFT_DATE) == self.NONE_SPECIFIED:
            draft_date = strftime("%Y/%m/%d")
        else:
            draft_date = wrapper.get_my_string(self.USER_SUPPLIED_DRAFT_DATE)
        if wrapper.get_my_string(self.REPORT_SIGNOFF_DATE) == self.NONE_SPECIFIED:
            report_signoff_date = strftime("%Y/%m/%d")
        else:
            report_signoff_date = wrapper.get_my_string(self.REPORT_SIGNOFF_DATE)
        self.check_assay_name(wrapper)
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {},
            'results': {
                self.ASSAY: wrapper.get_my_string(self.ASSAY),
                self.FAILED: wrapper.get_my_boolean(self.FAILED),
                core_constants.AUTHOR: config['core'][core_constants.AUTHOR],
                self.EXTRACT_DATE: draft_date,
                self.REPORT_SIGNOFF_DATE: report_signoff_date,
                self.GENETICIST: wrapper.get_my_string(self.GENETICIST),
                self.GENETICIST_ID: wrapper.get_my_string(self.GENETICIST_ID)
            },
            'version': str(self.SUPPLEMENT_DJERBA_VERSION)
        }
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)

    def specify_params(self):
        discovered = [
            self.ASSAY
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(self.REPORT_SIGNOFF_DATE, self.NONE_SPECIFIED)
        self.set_ini_default(self.USER_SUPPLIED_DRAFT_DATE, self.NONE_SPECIFIED)
        self.set_ini_default(self.GENETICIST, self.GENETICIST_DEFAULT)
        self.set_ini_default(self.GENETICIST_ID, self.GENETICIST_ID_DEFAULT)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(self.FAILED, "False")
        self.set_priority_defaults(self.DEFAULT_CONFIG_PRIORITY)
