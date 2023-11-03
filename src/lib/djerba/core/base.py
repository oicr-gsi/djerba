"""Base class for Djerba core with shared methods/constants"""

import csv
import re

import djerba.core.constants as core_constants
from djerba.util.logger import logger

class base(logger):

    @staticmethod
    def _is_helper_name(name):
        return re.search('_helper$', name)

    @staticmethod
    def _is_merger_name(name):
        return re.search('_merger$', name)

    @staticmethod
    def _is_null(param):
        return param == core_constants.NULL

    @staticmethod
    def _parse_comma_separated_list(list_string):
        # parse INI values stored as a comma-separated list -- eg. attributes, dependencies
        # use CSV reader to allow escaping and handle other edge cases
        # this method silently removes duplicates and sorts
        parsed = next(csv.reader([list_string]))
        parsed = sorted(list(set(parsed)))
        return parsed
