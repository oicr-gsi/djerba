#! /usr/bin/env python3

import mako
import os
import unittest
import djerba.util.ini_fields as ini

from configparser import ConfigParser

from djerba.util.benchmark import benchmarker
from djerba.util.render_mako import mako_renderer
from djerba.util.testing.tools import TestBase


class TestBenchmark(TestBase):

    class mock_report_args:
        """Use instead of argparse to store params for testing"""

        INPUT_DIR_VAR = 'DJERBA_GSICAPBENCH_INPUTS'

        def __init__(self, output_dir, dry_run):
            self.subparser_name = 'report'
            input_dir = os.environ.get(self.INPUT_DIR_VAR)
            if input_dir==None:
                raise RuntimeError("Need to set {0} env var".format(self.INPUT_DIR_VAR))
            elif not os.path.isdir(input_dir):
                raise OSError("Input dir '{0}' is not a directory".format(input_dir))
            else:
                self.input_dir = input_dir
            if not os.path.isdir(output_dir):
                raise OSError("Output dir '{0}' is not a directory".format(output_dir))
            else:
                self.output_dir = output_dir
            self.dry_run = dry_run
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = True # False # TODO FIXME
            self.quiet = True

    def test_report_dry_run(self):
        args = self.mock_report_args(self.tmp_dir, dry_run=True)
        benchmarker(args).run()
        for sample in benchmarker.SAMPLES:
            ini_path = os.path.join(self.tmp_dir, sample, 'config.ini')
            self.assertTrue(os.path.isfile(ini_path))
            cp = ConfigParser()
            cp.read(ini_path)
            sections = cp.sections()
            self.assertEqual(len(sections), 15)
            self.assertTrue('core' in sections)

    def test_report(self):
        args = self.mock_report_args(self.tmp_dir, dry_run=False)
        benchmarker(args).run()
        for sample in benchmarker.SAMPLES:
            json_path = os.path.join(self.tmp_dir, sample, 'report', 'djerba_report.json')
            self.assertTrue(os.path.isfile(json_path))
            # TODO diff this JSON against a previously generated reference file

class TestMakoRenderer(TestBase):

    def setUp(self):
        super().setUp() # includes tmp_dir
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))
    
    def test(self):
        mrend = mako_renderer(self.test_source_dir)
        test_template = mrend.get_template(self.test_source_dir, 'mako_template.html')
        self.assertIsInstance(test_template, mako.template.Template)
        args = {
            'greeting': 'Hello, world!'
        }
        with open(os.path.join(self.test_source_dir, 'mako_expected.html')) as in_file:
            expected_html = in_file.read()
        html_1 = mrend.render_template(test_template, args)
        self.assertEqual(html_1.strip(), expected_html.strip())
        html_2 = mrend.render_name('mako_template.html', args)
        self.assertEqual(html_2.strip(), expected_html.strip())

if __name__ == '__main__':
    unittest.main()

