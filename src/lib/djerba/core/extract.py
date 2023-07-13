"""
Class to initialize the data structure for the 'extract' step
The 'plugins' element is left empty, to be populated by the respective plugin classes
"""

import logging
import djerba.core.constants as cc
from djerba.core.base import base as core_base
from djerba.core.configure import config_wrapper

class extraction_setup(core_base):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def _get_core_params(self, config):
        core_params = {}
        core_config_keys = [
            cc.AUTHOR,
            cc.LOGO,
            cc.PREAMBLE,
            cc.STYLESHEET
        ]
        for key in core_config_keys:
            core_params[key] = config.get(cc.CORE, key)
        # TODO construct the report ID
        core_params[cc.REPORT_ID] = "placeholder"
        return core_params

    def _get_merger_params(self, config):
        mergers = {}
        for section_name in config.sections():
            if self._is_merger_name(section_name):
                merger_data = {}
                merger_data[cc.RENDER_PRIORITY] = \
                    config.getint(section_name, cc.RENDER_PRIORITY)
                attributes_str = config.get(section_name, cc.ATTRIBUTES)
                attributes = self._parse_comma_separated_list(attributes_str)
                merger_data[cc.ATTRIBUTES] = attributes
                mergers[section_name] = merger_data
        return mergers

    def run(self, config):
        """
        Construct a data framework containing:
        - Core parameters
        - Settings for mergers
        - Empty dictionary for plugin results
        - INI config parameters

        The framework will be populated by running the extract() methods of any configured plugins/helpers, in priority order.

        The core parameters include filenames for the logo, preamble, and stylesheet; these will be loaded at the render step.
        """
        data = {
            cc.CORE: self._get_core_params(config),
            cc.PLUGINS: {},
            cc.MERGERS: self._get_merger_params(config),
            cc.CONFIG: {s:dict(config.items(s)) for s in config.sections()}
        }
        return data


