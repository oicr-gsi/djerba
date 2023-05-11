"""Djerba plugin for pwgs supplement"""
import os
import logging

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
from djerba.core.workspace import workspace
import djerba.core.constants as core_constants

class main(plugin_base):

    DEFAULT_CONFIG_PRIORITY = 100

    def __init__(self, workspace, identifier, log_level=logging.INFO, log_path=None):
        super().__init__(workspace, identifier, log_level, log_path)
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)

    def configure(self, config):
        config = self.apply_defaults(config)
        config = self.set_all_priorities(config, self.DEFAULT_CONFIG_PRIORITY)
        return config

    def extract(self, config):
        data = {
            'plugin_name': self.identifier+' plugin',
            'priorities': self.get_my_priorities(config),
            'attributes': self.get_my_attributes(config),
            'merge_inputs': {
            },
            'results': {
                'author': config[self.identifier]['author']
            }
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
    
