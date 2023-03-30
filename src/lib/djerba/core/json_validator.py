"""Validate core/plugin JSON"""

# placeholder -- TODO add functionality based on bin/validate_plugin_json.py

import json
import jsonschema
import logging
import os
from djerba.util.logger import logger

class json_validator(logger):

    def __init__(self, schema_path, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.schema_path = schema_path
        with open(self.schema_path, 'r') as schema_file:
            self.schema = json.loads(schema_file.read())

    def validate_string(self, input_string):
        return self.validate_data(json.loads(input_string))

    def validate_data(self, data):
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.exceptions.ValidationError as err:
            msg = "JSON input is invalid with respect to "+\
                  "plugin schema {0}".format(self.schema_path)
            self.logger.error(msg)
            self.logger.error(err)
            raise
        msg = "JSON plugin data is valid with respect to schema {0}".format(self.schema_path)
        self.logger.info(msg)
        return True

class plugin_json_validator(json_validator):

    SCHEMA_FILENAME = 'plugin_schema.json'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        schema_path = os.path.join(os.path.dirname(__file__), self.SCHEMA_FILENAME)
        super().__init__(schema_path, log_level, log_path)
