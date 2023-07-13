"""
Class to initialize the data structure for the 'extract' step
The 'plugins' element is left empty, to be populated by the respective plugin classes
"""

import logging
import djerba.core.constants as core_constants
from djerba.core.base import base as core_base

class extraction_setup(core_base):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def _get_merger_params(self, config):
        mergers = {}
        for section_name in config.sections():
            if self._is_merger_name(section_name):
                merger_data = {}
                merger_data[core_constants.RENDER_PRIORITY] = \
                    config.getint(section_name, core_constants.RENDER_PRIORITY)
                attributes_str = config.get(section_name, core_constants.ATTRIBUTES)
                attributes = self._parse_comma_separated_list(attributes_str)
                merger_data[core_constants.ATTRIBUTES] = attributes
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
        # TODO make the 'core' data configurable
        data = {
            core_constants.CORE: {
                core_constants.ARCHIVE_NAME: "placeholder",
                core_constants.ARCHIVE_URL: "http://example.com/archive",
                core_constants.AUTHOR: "Test Author",
                core_constants.LOGO: "OICR_Logo_RGB_ENGLISH.png",
                core_constants.PREAMBLE: "preamble.html",
                core_constants.REPORT_ID: "placeholder",
                core_constants.STYLESHEET: "stylesheet.css"
            },
            core_constants.PLUGINS: {},
            core_constants.MERGERS: self._get_merger_params(config),
            core_constants.CONFIG: {s:dict(config.items(s)) for s in config.sections()}
        }
        return data


