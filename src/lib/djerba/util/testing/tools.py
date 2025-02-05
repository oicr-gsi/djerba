"""
Test base class
"""

import gzip
import hashlib
import re
import tempfile
import time
import unittest
import djerba.util.constants as constants
from djerba.util.validator import path_validator


class TestBase(unittest.TestCase):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def assert_report_MD5(self, report_string, expected_md5):
        body = self.redact_html(report_string)
        self.assertEqual(self.getMD5_of_string(body), expected_md5)

    def getMD5(self, inputPath):
        with open(inputPath, 'r') as f:
            md5sum = self.getMD5_of_string(f.read())
        return md5sum

    def getMD5_of_gzip_path(self, inputPath):
        # gzip compression is not deterministic -- need to uncompress first
        md5 = hashlib.md5()
        with gzip.open(inputPath, 'rt') as f:
            return self.getMD5_of_string(f.read())

    def getMD5_of_string(self, input_string):
        md5 = hashlib.md5()
        md5.update(input_string.encode(constants.TEXT_ENCODING))
        return md5.hexdigest()

    def get_tmp_dir(self):
        # convenience method; returns path to the temp dir
        return self.tmp_dir

    def redact_html(self, report_string):
        """
        Process HTML to remove elements unwanted for comparison, eg.report date
        May be overridden by test subclasses if needed
        """
        # based on check_report() from original djerba test.py
        # substitute out any date strings and check md5sum of the report body
        contents = re.split("\n", report_string)
        # crudely parse out the HTML body, omitting unwanted strings
        # could use an XML parser instead, but this way is simpler
        redacted_lines = []
        skip_exprs = [
            '<img.* src=',
            '<script',
            # IMPORTANT if text in supplement.body plugin is modified, update this expression
            '<p>Assay results were collated into the report document by '+\
            '<a href=https://github.com/oicr-gsi/djerba>Djerba</a> .* using pipeline .*</p>'
        ]
        for line in contents:
            if not any([re.search(expr, line) for expr in skip_exprs]):
                redacted_lines.append(line)
        redacted = ''.join(redacted_lines)
        redacted = re.sub('[0-9]{4}/[0-9]{2}/[0-9]{2}', '2000/01/01', redacted)
        redacted = re.sub('[0-9]{4}-[0-9]{2}-[0-9]{2}', '2000-01-01', redacted)
        return redacted

    def redact_json_data(self, data):
        """
        Placeholder method -- does nothing
        Can be overridden in subclasses to preprocess JSON data before test comparison
        IMPORTANT: If we return the input data object, changes to data will persist for downstream testing code. If this is not desired, use deepcopy to create a new instance of the data structure. See https://docs.python.org/3/library/copy.html and the supplement.body plugin in v1.8.0.
        """
        return data

    def redact_json_for_html(self, data):
        """
        Similar to redact_json_data, but applied before generating HTML with render()
        """
        return data
