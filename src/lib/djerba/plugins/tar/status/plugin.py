import logging

import djerba.core.constants as core_constants
from djerba.plugins.base import plugin_base
from djerba.core.workspace import workspace
from djerba.util.render_mako import mako_renderer

class main(plugin_base):

    COPY_NUMBER_CTDNA_DETECTED = 'copy_number_ctdna_detected'
    SMALL_MUTATION_CTDNA_DETECTED = 'small_mutation_ctdna_detected'
    ANY_CTDNA_DETECTED = 'any_ctdna_detected'
    # the above are all lower-case because they are used as JSON keys
    DETECTED_TEXT = 'ctDNA detected'
    NOT_DETECTED_TEXT = 'ctDNA not detected'
    PLUGIN_VERSION = '1.0.0'

    def configure(self, config):
        # only apply defaults here -- we either use default values or configure manually
        return self.apply_defaults(config)

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        cnv_detected = wrapper.get_my_boolean(self.COPY_NUMBER_CTDNA_DETECTED)
        snv_detected = wrapper.get_my_boolean(self.SMALL_MUTATION_CTDNA_DETECTED)
        any_detected = cnv_detected or snv_detected
        results = {
            self.COPY_NUMBER_CTDNA_DETECTED: self.get_detection_text(cnv_detected),
            self.SMALL_MUTATION_CTDNA_DETECTED: self.get_detection_text(snv_detected),
            self.ANY_CTDNA_DETECTED: 'Detected' if any_detected else 'Not Detected'
        }
        data['results'] = results
        return data

    def get_detection_text(self, detected):
        return self.DETECTED_TEXT if detected else self.NOT_DETECTED_TEXT
    
    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name('status_template.html', data)

    def specify_params(self):
        self.set_ini_default(self.COPY_NUMBER_CTDNA_DETECTED, False)
        self.set_ini_default(self.SMALL_MUTATION_CTDNA_DETECTED, False)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        # Default parameters for priorities
        self.set_ini_default('configure_priority', 300)
        self.set_ini_default('extract_priority', 300)
        self.set_ini_default('render_priority', 300)
