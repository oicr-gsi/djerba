"""Base class for Djerba core with shared methods/constants"""

import re

from djerba.util.logger import logger

class base(logger):
    
    @staticmethod
    def _is_helper_name(name):
        return re.search('_helper$', name)

    @staticmethod
    def _is_merger_name(name):
        return re.search('_merger$', name)
