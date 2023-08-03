"""Djerba plugin for pwgs supplement"""
import os
import logging

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 300

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Setting default parameters

    def specify_params(self):
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)
        
        # Setting required parameters
        self.add_ini_required('author')

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        wrapper.set_my_priorities(self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': wrapper.get_my_priorities(),
            'attributes': wrapper.get_my_attributes(),
            'merge_inputs': {
            },
            'results': {
                'author': config[self.identifier]['author']
            },
            'version': str(constants.PWGS_DJERBA_VERSION)
        }
        return data

    def render(self, data):
        args = data
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'html'
        ))
        report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
        mako_template = report_lookup.get_template(constants.SUPPLEMENT_TEMPLATE_NAME)
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            raise
        return html    
    
