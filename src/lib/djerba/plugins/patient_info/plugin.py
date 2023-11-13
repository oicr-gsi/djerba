"""Plugin to generate the "Patient & Physician Info" report section"""

import logging
import djerba.core.constants as core_constants
from email_validator import validate_email, EmailNotValidError
from time import strptime
from djerba.plugins.base import plugin_base

class main(plugin_base):

    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    DOB_DEFAULT = 'yyyy/mm/dd'
    PHONE_DEFAULT = 'nnn-nnn-nnnn'
    TEMPLATE_NAME = 'patient_info_template.html'

    # INI fields
    PATIENT_NAME = 'patient_name'
    PATIENT_DOB = 'patient_dob'
    PATIENT_SEX = 'patient_genetic_sex'
    REQ_EMAIL = 'requisitioner_email'
    PHYSICIAN_LICENCE = 'physician_licence_number'
    PHYSICIAN_NAME = 'physician_name'
    PHYSICIAN_PHONE = 'physician_phone_number'
    PHYSICIAN_HOSPITAL = 'hospital_name_and_address'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        email_input = wrapper.get_my_string(self.REQ_EMAIL)
        try:
            email_info = validate_email(email_input, check_deliverability=False)
            email = email_info.normalized
        except EmailNotValidError as err:
            msg = "Invalid email address for '{0}': {1}".format(self.REQ_EMAIL, err)
            self.logger.error(msg)
            raise
        wrapper.set_my_param(self.REQ_EMAIL, email)
        self.logger.debug('Validated requisitioner email')
        dob = wrapper.get_my_string(self.PATIENT_DOB)
        if dob != self.DOB_DEFAULT:
            try:
                time.strptime(dob, '%Y/%m/%d')
            except ValueError as err:
                msg = "Non-default value for '{0}' must be ".format(self.PATIENT_DOB)+\
                    "a date in yyyy/mm/dd format, got '{0}': {1}".format(dob, err)
                self.logger.error(msg)
                raise RuntimeError(msg) from err
            self.logger.debug('Validated patient DOB')
        else:
            self.logger.debug('Using DOB placeholder: {0}'.format(self.DOB_DEFAULT))
        # validating phone numbers is tricky, won't do it here
        # similarly, we will permit patient sex to be any string
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        # TODO new attribute to redact the uploaded JSON output
        attributes = wrapper.get_my_attributes()
        self.check_attributes_known(attributes)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        keys = [
            self.PATIENT_NAME,
            self.PATIENT_DOB,
            self.REQ_EMAIL,
            self.PHYSICIAN_LICENCE,
            self.PHYSICIAN_NAME,
            self.PHYSICIAN_PHONE,
            self.PHYSICIAN_HOSPITAL
        ]
        data['results'] = { k: wrapper.get_my_string(k) for k in keys }
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)

    def specify_params(self):
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(self.PATIENT_NAME, 'LAST, FIRST')
        self.set_ini_default(self.PATIENT_DOB, self.DOB_DEFAULT)
        self.set_ini_default(self.PATIENT_SEX, 'SEX')
        self.set_ini_default(self.REQ_EMAIL, 'NAME@DOMAIN.COM')
        self.set_ini_default(self.PHYSICIAN_LICENCE, 'nnnnnnnn')
        self.set_ini_default(self.PHYSICIAN_NAME, 'LAST, FIRST')
        self.set_ini_default(self.PHYSICIAN_PHONE, self.PHONE_DEFAULT)
        self.set_ini_default(self.PHYSICIAN_HOSPITAL, 'HOSPITAL NAME AND ADDRESS')
        self.set_priority_defaults(self.PRIORITY)
