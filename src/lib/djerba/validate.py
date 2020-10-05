

import json
import jsonschema
import logging
import os
from jsonschema.exceptions import ValidationError, SchemaError
from djerba.utilities.base import base
from djerba.utilities import constants

class validator(base):

    """Validate a Djerba config file; check schema format and existence of inputs"""

    SCHEMA_FILENAME = 'input_schema.json'
    
    def __init__(self, log_level=logging.WARN, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        schema_path = os.path.join(
            os.path.dirname(__file__),
            constants.DATA_DIRNAME,
            self.SCHEMA_FILENAME
        )
        with open(schema_path, 'r') as schema_file:
            self.schema = json.loads(schema_file.read())

    def validate(self, config, sample_name):
        """Check the config data structure against the schema"""
        try:
            jsonschema.validate(config, self.schema)
            self.logger.debug("Djerba config is valid with respect to schema")
        except (ValidationError, SchemaError) as err:
            msg = "Djerba config is invalid with respect to schema"
            self.logger.error("{}: {}".format(msg, err))
            raise DjerbaConfigError(msg) from err
        if sample_name != None:
            sample_name_found = False
            for sample in config[constants.SAMPLES_KEY]:
                if sample[constants.SAMPLE_ID_KEY] == sample_name:
                    sample_name_found = True
                    self.logger.debug(
                        "Required sample name '{}' found in Djerba config".format(sample_name)
                    )
                    break
            if not sample_name_found:
                msg = "Required sample name '{}' not found in config".format(sample_name)
                self.logger.error(msg)
                raise DjerbaConfigError(msg)
        else:
            self.logger.debug("No sample name supplied, omitting check")
        self.logger.info("Djerba config is valid")
        return True

class DjerbaConfigError(Exception):
    pass
