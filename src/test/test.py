#! /usr/bin/env python3

import configparser
import hashlib
import json
import jsonschema
import logging
import os
import subprocess
import tempfile
import unittest
import djerba.util.constants as constants
from djerba.configure import configurer
from djerba.extract.extractor import extractor
from djerba.extract.report_directory_parser import report_directory_parser
from djerba.extract.sequenza import sequenza_extractor, SequenzaExtractionError
from djerba.extract.r_script_wrapper import r_script_wrapper
from djerba.main import main
from djerba.render import html_renderer, pdf_renderer
from djerba.util.validator import config_validator, DjerbaConfigError

class TestBase(unittest.TestCase):

    def getMD5(self, inputPath):
        md5 = hashlib.md5()
        with open(inputPath, 'rb') as f:
            md5.update(f.read())
        return md5.hexdigest()

    def run_command(self, cmd):
        """Run a command; in case of failure, capture STDERR."""
        result = subprocess.run(cmd, encoding=constants.TEXT_ENCODING, capture_output=True)
        try:
            result.check_returncode()
        except subprocess.CalledProcessError as err:
            msg = "Script failed with STDERR: "+result.stderr
            raise RuntimeError(msg) from err
        return result

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        # specify all non-public data paths relative to self.sup_dir
        # modified test provenance file gets its own environment variable
        sup_dir_var = 'DJERBA_TEST_DATA'
        provenance_var = 'DJERBA_TEST_PROVENANCE'
        self.sup_dir = os.environ.get(sup_dir_var)
        self.provenance_path = os.environ.get(provenance_var)
        if not (self.sup_dir):
            raise RuntimeError('Need to specify environment variable {0}'.format(sup_dir_var))
        elif not os.path.isdir(self.sup_dir):
            raise OSError("Supplementary directory path '{0}' is not a directory".format(self.sup_dir))
        if not self.provenance_path:
            raise RuntimeError('Need to specify environment variable {0}'.format(provenance_var))
        elif not os.path.isfile(self.provenance_path):
            raise OSError("Provenance path '{0}' is not a file".format(self.provenance_path))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmpDir = self.tmp.name
        self.schema_path = os.path.join(self.sup_dir, 'elba_config_schema.json')
        self.bed_path = os.path.join(self.sup_dir, 'S31285117_Regions.bed')
        self.maf_name = 'PANX_1249_Lv_M_WG_100-PM-013_LCM5.filter.deduped.realigned.recalibrated.mutect2.tumor_only.filtered.unmatched.maf.gz'
        self.expected_maf_path = os.path.join(self.sup_dir, self.maf_name)
        self.project = 'PASS01'
        self.donor = 'PANX_1249'
        with open(self.schema_path) as f:
            self.schema = json.loads(f.read())
        self.rScriptDir = os.path.realpath(os.path.join(self.testDir, '../lib/djerba/R/'))
        self.default_ini = os.path.realpath(os.path.join(self.testDir, '../lib/djerba/data/defaults.ini'))

    def tearDown(self):
        self.tmp.cleanup()

class TestConfigure(TestBase):

    def setUp(self):
        super().setUp()
        self.iniPath = os.path.join(self.dataDir, 'config_user.ini')

    def test_configurer(self):
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(self.iniPath)
        config['settings']['provenance'] = os.path.join(self.sup_dir, 'pass01_panx_provenance.original.tsv.gz')
        test_configurer = configurer(config, log_level=logging.ERROR)
        out_dir = self.tmpDir
        out_path = os.path.join(out_dir, 'config_test_output.ini')
        test_configurer.run(out_path)
        # TODO check contents of output path; need to account for supplementary data location
        self.assertTrue(os.path.exists(out_path))

class TestExtractor(TestBase):

    def setUp(self):
        super().setUp()
        self.iniPath = os.path.join(self.dataDir, 'config_full.ini')

    def test_extractor(self):
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(self.iniPath)
        out_dir = '/u/ibancarz/workspace/djerba/TestExtractor'  # self.tmpDir
        clinical_data_path = os.path.join(out_dir, 'data_clinical.txt')
        summary_path = os.path.join(out_dir, 'summary.json')
        test_extractor = extractor(config, out_dir, log_level=logging.ERROR)
        # do not test R script here; done by TestWrapper
        test_extractor.run(summary_path, r_script=False)
        self.assertTrue(os.path.exists(clinical_data_path))
        self.assertTrue(os.path.exists(summary_path))
        self.assertEqual(self.getMD5(clinical_data_path), '02003366977d66578c097295f12f4638')
        self.assertEqual(self.getMD5(summary_path), '9945fa608f8960964e967f7aecd8fda7')

class TestMain(TestBase):

    class mock_args:
        """Use instead of argparse to store params for testing"""

        def __init__(self, ini_path, ini_out_path, html_path, pdf_path, work_dir):
            self.ini_out = ini_out_path
            self.dir = work_dir
            self.html = html_path
            self.ini = ini_path
            self.pdf = pdf_path
            self.json = None
            self.subparser_name = constants.ALL
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_main(self):
        out_dir = '/u/ibancarz/workspace/djerba/TestMain'
        ini_path = os.path.join(self.dataDir, 'config_user.ini')
        config_path = os.path.join(out_dir, 'config.ini')
        html_path = os.path.join(out_dir, 'report.html')
        pdf_path = os.path.join(out_dir, 'report.pdf')
        work_dir = os.path.join(out_dir, 'report')
        if not os.path.exists(work_dir):
            os.mkdir(work_dir)
        args = self.mock_args(ini_path, config_path, html_path, pdf_path, work_dir)
        main().run(args)

class TestRender(TestBase):

    def test_html(self):
        outDir = self.tmpDir
        outPath = os.path.join(outDir, 'djerba_test.html')
        reportDir = os.path.join(self.sup_dir, 'report_example')
        html_renderer(log_level=logging.ERROR).run(reportDir, outPath)
        # TODO check file contents; need to omit the report date etc.
        self.assertTrue(os.path.exists(outPath))

    @unittest.SkipTest
    def test_pdf(self):
        # TODO omit this test until wkhtmltopdf is installed
        in_path = os.path.join(self.sup_dir, 'djerba_test.html')
        #out_dir = self.tmpDir
        out_dir = '/u/ibancarz/workspace/djerba/TestRender'
        out_path = os.path.join(out_dir, 'djerba_test.pdf')
        test_renderer = pdf_renderer(log_level=logging.ERROR)
        test_renderer.run(in_path, out_path)
        self.assertTrue(os.path.exists(out_path))

class TestReport(TestBase):

    def test_parser(self):
        report_dir = os.path.join(self.sup_dir, 'report_for_parser_test')
        parser = report_directory_parser(report_dir)
        summary = parser.get_summary()
        expected_path = os.path.join(self.sup_dir, 'expected_summary.json')
        with open(expected_path) as expected_file:
            expected = json.loads(expected_file.read())
        self.assertEqual(summary, expected)

class TestSequenzaExtractor(TestBase):

    def setUp(self):
        super().setUp()
        self.zip_path = os.path.join(self.sup_dir, 'PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip')
        self.expected_gamma_id = (400, 'primary')

    def test_finder_script(self):
        """Test the command-line script to find gamma"""
        json_path = os.path.join(self.tmpDir, 'sequenza_gamma.json')
        cmd = [
            "sequenza_solutions.py",
            "--in", self.zip_path,
            "--json", json_path,
            "--gamma-selection",
            "--purity-ploidy",
            "--summary"
        ]
        result = self.run_command(cmd)
        with open(os.path.join(self.dataDir, 'expected_sequenza.txt'), 'rt') as in_file:
            expected_text = in_file.read()
        self.assertEqual(result.stdout, expected_text)
        expected_json = os.path.join(self.dataDir, 'expected_sequenza.json')
        with open(expected_json, 'rt') as exp_file, open(json_path, 'rt') as out_file:
            output = json.loads(out_file.read())
            expected = json.loads(exp_file.read())
            self.assertEqual(output, expected)

    def test_purity_ploidy(self):
        seqex = sequenza_extractor(self.zip_path)
        self.assertEqual(seqex.get_purity(), 0.6)
        self.assertEqual(seqex.get_ploidy(), 3.1)
        expected_segments = {
            (100, 'primary'): 4356,
            (100, 'sol2_0.59'): 4356,
            (1000, 'sol3_0.42'): 245,
            (1000, 'sol4_0.73'): 245,
            (1000, 'primary'): 245,
            (1000, 'sol2_0.49'): 245,
            (1250, 'sol3_0.42'): 165,
            (1250, 'sol4_0.73'): 165,
            (1250, 'sol5_0.4'): 165,
            (1250, 'primary'): 165,
            (1250, 'sol2_0.49'): 165,
            (1500, 'sol2_0.48'): 123,
            (1500, 'sol3_0.42'): 123,
            (1500, 'sol5_0.4'): 123,
            (1500, 'primary'): 123,
            (1500, 'sol4_0.72'): 123,
            (200, 'sol2_0.24'): 1955,
            (200, 'primary'): 1955,
            (200, 'sol3_0.31'): 1955,
            (2000, 'sol2_0.42'): 84,
            (2000, 'sol6_0.39'): 84,
            (2000, 'sol3_0.48'): 84,
            (2000, 'primary'): 84,
            (2000, 'sol4_1'): 84,
            (2000, 'sol5_0.72'): 84,
            (300, 'sol4_0.43'): 1170,
            (300, 'sol2_0.32'): 1170,
            (300, 'sol3_0.24'): 1170,
            (300, 'primary'): 1170,
            (400, 'sol3_0.43'): 839,
            (400, 'primary'): 839,
            (400, 'sol4_1'): 839,
            (400, 'sol2_0.44'): 839,
            (400, 'sol5_0.39'): 839,
            (50, 'primary'): 8669,
            (500, 'sol2_0.48'): 622,
            (500, 'sol3_0.42'): 622,
            (500, 'primary'): 622,
            (500, 'sol4_0.39'): 622,
            (600, 'sol2_0.48'): 471,
            (600, 'sol3_0.42'): 471,
            (600, 'sol4_0.73'): 471,
            (600, 'primary'): 471,
            (700, 'sol2_0.48'): 407,
            (700, 'sol3_0.42'): 407,
            (700, 'sol4_0.73'): 407,
            (700, 'primary'): 407,
            (800, 'sol3_0.42'): 337,
            (800, 'sol4_0.73'): 337,
            (800, 'primary'): 337,
            (800, 'sol2_0.49'): 337,
            (900, 'sol3_0.42'): 284,
            (900, 'sol4_0.73'): 284,
            (900, 'primary'): 284,
            (900, 'sol2_0.49'): 284
        }
        self.assertEqual(seqex.get_segment_counts(), expected_segments)
        self.assertEqual(seqex.get_default_gamma_id(), self.expected_gamma_id)
        # test with alternate gamma
        self.assertEqual(seqex.get_purity(gamma=50), 0.56)
        self.assertEqual(seqex.get_ploidy(gamma=50), 3.2)
        # test with nonexistent gamma
        with self.assertRaises(SequenzaExtractionError):
            seqex.get_purity(gamma=999999)
        with self.assertRaises(SequenzaExtractionError):
            seqex.get_ploidy(gamma=999999)

    def test_seg_file(self):
        seqex = sequenza_extractor(self.zip_path)
        seg_path = seqex.extract_seg_file(self.tmpDir)
        self.assertEqual(
            seg_path,
            os.path.join(self.tmpDir, 'gammas/400/PANX_1249_Lv_M_WG_100-PM-013_LCM5_Total_CN.seg')
        )
        self.assertEqual(self.getMD5(seg_path), '25b0e3c01fe77a28b24cff46081cfb1b')
        seg_path = seqex.extract_seg_file(self.tmpDir, gamma=1000)
        self.assertEqual(
            seg_path,
            os.path.join(self.tmpDir, 'gammas/1000/PANX_1249_Lv_M_WG_100-PM-013_LCM5_Total_CN.seg')
        )
        self.assertEqual(self.getMD5(seg_path), '5d433e47431029219b6922fba63a8fcf')
        with self.assertRaises(SequenzaExtractionError):
            seqex.extract_seg_file(self.tmpDir, gamma=999999)

class TestValidator(TestBase):

    def test_config_validator(self):
        config_user = configparser.ConfigParser()
        config_user.read(os.path.join(self.dataDir, 'config_user.ini'))
        config_full = configparser.ConfigParser()
        config_full.read(os.path.join(self.dataDir, 'config_full.ini'))
        validator = config_validator(log_level=logging.ERROR)
        self.assertTrue(validator.validate_minimal(config_user))
        self.assertTrue(validator.validate_full(config_full))
        # minimal config will fail the validate_full check
        validator_critical = config_validator(log_level=logging.CRITICAL)
        with self.assertRaises(DjerbaConfigError):
            self.assertTrue(validator_critical.validate_full(config_user))

class TestWrapper(TestBase):

    def test(self):
        iniPath = os.path.join(self.sup_dir, 'rscript_config_updated.ini')
        config = configparser.ConfigParser()
        config.read(iniPath)
        out_dir = '/u/ibancarz/workspace/djerba/TestWrapper' # TODO change to tempdir
        test_wrapper = r_script_wrapper(config, gamma=500, report_dir=out_dir)
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)

if __name__ == '__main__':
    unittest.main()
