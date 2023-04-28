"""Base class for all components: Plugins, helpers, mergers"""

from abc import ABC
from djerba.util.logger import logger

class component(logger, ABC):

    DEFAULT_CONFIG_PRIORITY = 10000 # override in subclasses

    def get_default_config_priority(self):
        return self.DEFAULT_CONFIG_PRIORITY
