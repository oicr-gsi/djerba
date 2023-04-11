"""
Test base class; called 'trial.py' to hide from automated unittest discovery
"""

import hashlib
import re
import time
import unittest
import djerba.util.constants as constants
from djerba.util.validator import path_validator


class TestBase(unittest.TestCase):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None

    def assert_report_MD5(self, report_string, expected_md5):
        body = self.redact_html(report_string)
        self.assertEqual(self.getMD5_of_string(body), expected_md5)
    
    def getMD5(self, inputPath):
        with open(inputPath, 'rb') as f:
            md5sum = getMD5_of_string(f.read())
        return md5sum

    def getMD5_of_string(self, input_string):
        md5 = hashlib.md5()
        md5.update(input_string.encode(constants.TEXT_ENCODING))
        return md5.hexdigest()

    def redact_html(self, report_string):
        """
        Process HTML to remove elements unwanted for comparison, eg.report date
        May be overridden by test subclasses if needed
        """
        # based on check_report() from original djerba test.py
        # substitute out any date strings and check md5sum of the report body
        contents = re.split("\n", report_string)
        # crudely parse out the HTML body, omitting <img> tags
        # could use an XML parser instead, but this way is simpler
        redacted_lines = []
        for line in contents:
            if not re.search('<img src=', line) and not re.search('<script', line):
                redacted_lines.append(line)
        redacted = ''.join(redacted_lines)
        redacted = redacted.replace(time.strftime("%Y/%m/%d"), '0000/00/31')
        return redacted

    def redact_json_data(self, data):
        """
        Placeholder method -- does nothing
        Can be overridden in subclasses to preprocess JSON data before test comparison
        """
        return data
