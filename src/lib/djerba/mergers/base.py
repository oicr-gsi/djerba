"""
Abstract base class for mergers
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
import os
from abc import ABC
from djerba.core.configure import configurable
from djerba.core.json_validator import json_validator
from djerba.util.html import html_builder
from djerba.util.logger import logger
import djerba.core.constants as core_constants

class merger_base(configurable, html_builder, ABC):

    SCHEMA_NAME = 'merger_schema.json'

    PRIORITY_KEYS = [
        core_constants.CONFIGURE_PRIORITY,
        core_constants.RENDER_PRIORITY
    ] # extract priority is not defined for mergers

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        schema_path = os.path.join(self.module_dir, self.SCHEMA_NAME)
        # global defaults for mergers; can override for individual merger classes
        self.json_validator = json_validator(schema_path, self.log_level, self.log_path)
        self.ini_defaults = {
            core_constants.ATTRIBUTES: '',
            core_constants.DEPENDS_CONFIGURE: '',
            core_constants.CONFIGURE_PRIORITY: 1000,
            core_constants.RENDER_PRIORITY: 1000
        }
        self.attributes = []
        self.specify_params()

    def get_unique_dicts(self, inputs, primary_key):
        # get unique dictionaries from the list, see https://stackoverflow.com/a/11092590
        try:
            unique_items = list({v[primary_key]:v for v in inputs}.values())
        except KeyError:
            msg = "Primary key {0} is missing from at least one input ".format(primary_key)+\
                  "to merger; run in debug mode to view inputs"
            self.logger.error(msg)
            self.logger.debug("Merger inputs: {0}".format(inputs))
            raise
        return unique_items

    def merge_and_sort(self, inputs_list, sort_key):
        """
        Merge a list of inputs matching the schema, remove duplicates, sort by given key
        Assumes the sort key is also a unique identifier for deduplication
        """
        # input is a list of lists, flatten into a single list
        flattened = [x for sublist in inputs_list for x in sublist]
        unique_items = self.get_unique_dicts(flattened, sort_key)
        return sorted(unique_items, key = lambda x: x[sort_key])

    def render(self, inputs):
        """
        Input is a list of data structures, obtained one or more plugins
        Each input structure must match the schema for this merger
        Output is a string (for inclusion in an HTML document)
        """
        msg = "Using method of parent class; checks inputs and returns empty string"
        self.logger.debug(msg)
        for item in inputs:
            self.json_validator.validate_data(item)
        return ''

    def set_priority_defaults(self, priority):
        for key in self.PRIORITY_KEYS:
            self.ini_defaults[key] = priority

    def validate_inputs(self, inputs):
        for item in inputs:
            self.json_validator.validate_data(item)
        self.logger.info("All merger inputs validated")

