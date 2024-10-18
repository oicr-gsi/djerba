"""
Class to initialize the data structure for the 'extract' step
The 'plugins' element is left empty, to be populated by the respective plugin classes
"""

import logging
import time
import djerba.core.constants as cc
from djerba.core.base import base as core_base
from djerba.core.configure import config_wrapper
from djerba.util.date import get_timestamp
from djerba.version import get_djerba_version

class extraction_setup(core_base):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def _get_core_params(self, config):
        core_config_keys = [
            cc.AUTHOR,
            cc.DOCUMENT_CONFIG,
            cc.REPORT_ID
        ]
        core_params = {x: config.get(cc.CORE, x) for x in core_config_keys}
        # add the core release version
        core_params[cc.CORE_VERSION] = get_djerba_version()
        # add the timestamp in UTC
        core_params[cc.EXTRACT_TIME] = get_timestamp()
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

        The framework will be populated by running the extract() methods of any
        configured plugins/helpers, in priority order.
        """
        data = {
            cc.CORE: self._get_core_params(config),
            cc.PLUGINS: {},
            cc.MERGERS: self._get_merger_params(config),
            cc.CONFIG: {s:dict(config.items(s)) for s in config.sections()},
            cc.HTML_CACHE: {}
        }
        return data


