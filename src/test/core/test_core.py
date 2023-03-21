#! /usr/bin/env python3

import hashlib
import json
import jsonschema
import logging
import os
import unittest

from djerba.core.json_validator import json_validator
from djerba.core.main import main
import djerba.util.constants as constants

class TestBase(unittest.TestCase):

    def getMD5(self, inputPath):
        with open(inputPath, 'rb') as f:
            md5sum = getMD5_of_string(f.read())
        return md5sum

    def getMD5_of_string(self, input_string):
        md5 = hashlib.md5()
        md5.update(input_string.encode(constants.TEXT_ENCODING))
        return md5.hexdigest()


class TestValidator(TestBase):

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

class TestSimpleReport(TestBase):

    def test_report(self):
        ini_path = os.path.join(os.path.dirname(__file__), 'test.ini')
        json_path = os.path.join(os.path.dirname(__file__), 'simple_report_expected.json')
        djerba_main = main(log_level=logging.WARNING)
        config = djerba_main.configure(ini_path)
        data_found = djerba_main.extract(config)
        with open(json_path) as json_file:
            data_expected = json.loads(json_file.read())
        self.assertEqual(data_found, data_expected)
        html = djerba_main.render(data_found)
        self.assertEqual(self.getMD5_of_string(html), 'bc8017b0addfbf69d3d44e3a60c28ff4')

if __name__ == '__main__':
    unittest.main()
