#! /usr/bin/env python3

import json
import jsonschema
import logging
import os
import unittest

from djerba.core.json_validator import json_validator

class TestCore(unittest.TestCase):

    EXAMPLE_DEFAULT = 'plugin_example.json'
    EXAMPLE_EMPTY = 'plugin_example_empty.json'
    EXAMPLE_BROKEN = 'plugin_example_broken.json'
    
    def test_plugin(self):
        validator = json_validator(log_level=logging.WARNING)
        for filename in [self.EXAMPLE_DEFAULT, self.EXAMPLE_EMPTY]:
            in_path = os.path.join(os.path.dirname(__file__), filename)
            with open(in_path) as in_file:
                input_data = json.loads(in_file.read())
            self.assertTrue(validator.validate_data(input_data))

    def test_plugin_broken(self):
        validator = json_validator(log_level=logging.CRITICAL)
        in_path = os.path.join(os.path.dirname(__file__), self.EXAMPLE_BROKEN)
        with open(in_path) as in_file:
            input_data = json.loads(in_file.read())
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validator.validate_data(input_data)

if __name__ == '__main__':
    unittest.main()
