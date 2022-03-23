#! /usr/bin/env python3

import configparser
import gzip
import hashlib
import json
import logging
import os
import re
import subprocess
import tempfile
import time
import unittest
from string import Template

import djerba.util.constants as constants
from djerba.configure import archiver, configurer, log_r_cutoff_finder
from djerba.extract.extractor import extractor
from djerba.extract.report_directory_parser import report_directory_parser
from djerba.extract.r_script_wrapper import r_script_wrapper
from djerba.lister import lister
from djerba.main import main
from djerba.mavis import mavis_runner
from djerba.render import html_renderer, pdf_renderer
from djerba.sequenza import sequenza_reader, SequenzaError
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
        test_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.realpath(os.path.join(test_dir, 'data'))
        # specify all non-public data paths relative to self.sup_dir
        sup_dir_var = 'DJERBA_TEST_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)
        if not (self.sup_dir):
            raise RuntimeError('Need to specify environment variable {0}'.format(sup_dir_var))
        elif not os.path.isdir(self.sup_dir):
            raise OSError("Supplementary directory path '{0}' is not a directory".format(self.sup_dir))
        self.provenance = os.path.join(self.sup_dir, 'pass01_panx_provenance.original.tsv.gz')
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.bed_path = os.path.join(self.sup_dir, 'S31285117_Regions.bed')
        self.project = 'PASS01'
        self.donor = 'PANX_1249'
        self.rScriptDir = os.path.realpath(os.path.join(test_dir, '../lib/djerba/R/'))
        self.lib_data = os.path.realpath(os.path.join(test_dir, '../lib/djerba/data')) # installed data files from src/lib
        self.default_ini = os.path.realpath(os.path.join(self.lib_data, 'defaults.ini'))
        [
            self.config_user,
            self.config_user_wgs_only,
            self.config_user_failed,
            self.config_user_wgs_only_failed,
            self.config_full,
            self.config_full_wgs_only
        ] = self.write_config_files(self.tmp_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def write_config_files(self, output_dir):
        """
        Use Python string templates to write customized test config files
        """
        settings = {
            "SUPPLEMENTARY": self.sup_dir,
            "LIB_DATA": self.lib_data
        }
        out_paths = []
        for name in [
                'config_user.ini',
                'config_user_wgs_only.ini',
                'config_user_failed.ini',
                'config_user_wgs_only_failed.ini',
                'config_full.ini',
                'config_full_wgs_only.ini'
        ]:
            template_path = os.path.join(self.data_dir, name)
            out_path = os.path.join(output_dir, name)
            with open(template_path) as in_file, open(out_path, 'w') as out_file:
                src = Template(in_file.read())
                out_file.write(src.substitute(settings))
            out_paths.append(out_path)
        return out_paths

class TestArchive(TestBase):

    def test_archive(self):
        out_dir = self.tmp_dir
        archive_path = archiver(self.config_full).run(out_dir)
        # contents of file are dependent on local paths
        self.assertTrue(os.path.exists(archive_path))
        with open(archive_path) as archive_file:
            lines = len(archive_file.readlines())
        self.assertEqual(lines, 50)

class TestConfigure(TestBase):

    def run_config_test(self, user_config, wgs_only, failed, expected_lines):
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(user_config)
        config['settings']['provenance'] = self.provenance
        test_configurer = configurer(config, wgs_only, failed)
        out_dir = self.tmp_dir
        out_path = os.path.join(out_dir, 'config_test_output.ini')
        test_configurer.run(out_path, archive=False)
        # TODO check contents of output path; need to account for supplementary data location
        self.assertTrue(os.path.exists(out_path))
        with open(out_path) as out_file:
            lines = len(out_file.readlines())
        self.assertEqual(lines, expected_lines) # unlike archive, configParser puts a blank line at the end of the file

    def test_default(self):
        self.run_config_test(self.config_user, False, False, 51)

    def test_default_fail(self):
        self.run_config_test(self.config_user_failed, False, True, 41)

    def test_wgs_only(self):
        self.run_config_test(self.config_user_wgs_only, True, False, 49)

    def test_wgs_only_fail(self):
        self.run_config_test(self.config_user_wgs_only_failed, True, True, 41)


class TestCutoffFinder(TestBase):

    def test_cutoffs(self):
        purity = 0.65
        expected = {
            'htzd': -0.28352029636194687,
            'hmzd': -1.0408068827768262,
            'gain': 0.2029961798379184,
            'ampl': 0.5642291920734639
        }
        cutoffs = log_r_cutoff_finder().cutoffs(purity)
        for key in expected.keys():
            self.assertAlmostEqual(expected[key], cutoffs[key])

class TestExtractor(TestBase):

    # this test does not check the R script
    # so outputs for WGS-only and WGS+WTS are identical

    def run_extractor_test(self, user_config, wgs_only, failed):
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(user_config)
        out_dir = self.tmp_dir
        clinical_data_path = os.path.join(out_dir, 'data_clinical.txt')
        summary_path = os.path.join(out_dir, 'summary.json')
        test_extractor = extractor(config, out_dir, wgs_only, failed, log_level=logging.ERROR)
        # do not test R script or JSON here; done respectively by TestWrapper and TestReport
        test_extractor.run(json_path=None, r_script=False)
        expected_md5 = {
            'data_clinical.txt': '02003366977d66578c097295f12f4638',
            'genomic_summary.txt': 'c84eec523dbc81f4fc7b08860ab1a47f'
        }
        for filename in expected_md5.keys():
            output_path = os.path.join(out_dir, filename)
            self.assertTrue(os.path.exists(output_path))
        self.assertEqual(self.getMD5(output_path), expected_md5[filename])

    def test_extractor(self):
        self.run_extractor_test(self.config_full, False, False)

    def test_extractor_failed(self):
        self.run_extractor_test(self.config_full, False, True)

    def test_extractor_wgs_only(self):
        self.run_extractor_test(self.config_full_wgs_only, True, False)

    def test_extractor_wgs_only_failed(self):
        self.run_extractor_test(self.config_full_wgs_only, True, True)

class TestLister(TestBase):

    class mock_args:
        """Use instead of argparse to store params for testing"""

        def __init__(self, ini_path, out_path, donor, project, provenance):
            self.ini = ini_path
            self.output = out_path
            self.donor = donor
            self.study = project
            self.provenance = provenance
            self.wgs_only = False
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_lister(self):
        out_path = os.path.join(self.tmp_dir, 'inputs.txt')
        args = self.mock_args(self.config_full, out_path, self.donor, self.project, self.provenance)
        lister(args).run()
        self.assertTrue(os.path.exists(out_path))
        with open(out_path) as out_file:
            output = out_file.read()
        with open(os.path.join(self.sup_dir, 'input_list.txt')) as expected_file:
            expected = expected_file.read()
            expected = expected.replace('PLACEHOLDER', self.sup_dir)
        self.assertEqual(output, expected)

class TestMain(TestBase):

    class mock_args:
        """Use instead of argparse to store params for testing"""

        def __init__(self, ini_path, ini_out_path, html_path, work_dir):
            self.ini_out = ini_out_path
            self.author = None
            self.dir = work_dir
            self.failed = False
            self.html = html_path
            self.ini = ini_path
            self.target_coverage = 40
            self.json = None
            self.pdf = None
            self.subparser_name = constants.ALL
            self.no_archive = True
            self.wgs_only = False
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_main(self):
        out_dir = self.tmp_dir
        ini_path = self.config_user
        config_path = os.path.join(out_dir, 'config.ini')
        html_path = os.path.join(out_dir, 'report.html')
        work_dir = os.path.join(out_dir, 'report')
        patient_id = '100-PM-013'
        if not os.path.exists(work_dir):
            os.mkdir(work_dir)
        args = self.mock_args(ini_path, config_path, html_path, work_dir)
        main(args).run()
        self.assertTrue(os.path.exists(html_path))
        pdf_path = os.path.join(work_dir, '{0}_djerba_report.pdf'.format(patient_id))
        self.assertTrue(os.path.exists(pdf_path))

class TestMavis(TestBase):

    class mock_mavis_args:

        def __init__(self, work_dir, donor, study):
            self.config = None
            self.dry_run = False
            self.execute = False
            self.legacy = False
            self.ready = True
            self.work_dir = work_dir
            self.donor = donor
            self.study = study
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

        def set_to_execute_dry_run(self):
            self.dry_run = True
            self.execute = True
            self.ready = False

    def test_ready(self):
        out_dir = self.tmp_dir
        mock_args = self.mock_mavis_args(out_dir, self.donor, self.project)
        self.run_test(mock_args, out_dir)

    def test_ready_legacy(self):
        out_dir = self.tmp_dir
        mock_args = self.mock_mavis_args(out_dir, self.donor, self.project)
        mock_args.legacy = True
        self.run_test(mock_args, out_dir)

    def run_test(self, mock_args, out_dir):
        runner = mavis_runner(mock_args)
        runner.provenance_path = self.provenance
        action = runner.main()
        self.assertEqual(action, 1)
        filenames = [
            'mavis_cromwell.json',
            'PANX_1249_Lv_M_WT_100-PM-013_LCM5.Aligned.sortedByCoord.out.bai',
            'PANX_1249_Lv_M_WT_100-PM-013_LCM5.Aligned.sortedByCoord.out.bam',
            'PANX_1249_Lv_M_WG_100-PM-013_LCM5_somatic.somatic_filtered.delly.merged.vcf.gz',
            'PANX_1249_Lv_M_WT_100-PM-013_LCM5.fusions.tsv',
            'star-fusion.fusion_predictions.tsv'
        ]
        for name in filenames:
            self.assertTrue(os.path.exists(os.path.join(out_dir, name)))
        # test execute in dry-run mode; live test is separate
        mock_args.set_to_execute_dry_run()
        runner = mavis_runner(mock_args)
        runner.provenance_path = self.provenance
        action = runner.main()
        self.assertEqual(action, 2)

class TestRender(TestBase):

    def check_report(self, report_path, expected_md5):
        # substitute out any date strings and check md5sum of the report body
        with open(report_path) as report_file:
            contents = report_file.readlines()
        # crudely parse out the HTML body, omitting <img> tags
        # could use an XML parser instead, but this way is simpler
        body_lines = []
        in_body = False
        for line in contents:
            if re.search('<body>', line):
                in_body = True
            elif re.search('</body>', line):
                break
            elif in_body and not re.search('<img src=', line):
                body_lines.append(line)
        body = ''.join(body_lines)
        body = body.replace(time.strftime("%Y/%m/%d"), '0000/00/31')
        md5 = hashlib.md5(body.encode(encoding=constants.TEXT_ENCODING)).hexdigest()
        self.assertEqual(md5, expected_md5)

    def test_html(self):
        #outDir = self.tmp_dir
        outDir = '/u/ibancarz/workspace/djerba/test_20220307_02'
        outPath = os.path.join(outDir, 'djerba_test.html')
        reportDir = os.path.join(self.sup_dir, 'report_example')
        html_renderer(wgs_only=False, failed=False, log_level=logging.ERROR).run(reportDir, outPath, target_coverage=40)
        # check file contents; need to omit the report date etc.
        self.assertTrue(os.path.exists(outPath))
        self.check_report(outPath, 'da3c4a868084586e5c95df6d6f428b09')
        failPath = os.path.join(outDir, 'djerba_fail_test.html')
        html_renderer(wgs_only=False, failed=True, log_level=logging.ERROR).run(reportDir, failPath, target_coverage=40)
        self.assertTrue(os.path.exists(failPath))
        self.check_report(failPath, 'ab9c15bac07cb9ce56d33b112e2644ce')
        failPath = os.path.join(outDir, 'djerba_fail_wgs_test.html')
        html_renderer(wgs_only=True, failed=True, log_level=logging.ERROR).run(reportDir, failPath, target_coverage=40)
        self.assertTrue(os.path.exists(failPath))
        self.check_report(failPath, '67c088d38641f346def5ec5802e38bd4')
        wgsOnlyPath = os.path.join(outDir, 'djerba_wgs_only_test.html')
        html_renderer(wgs_only=True, failed=False, log_level=logging.ERROR).run(reportDir, wgsOnlyPath, target_coverage=40)
        self.assertTrue(os.path.exists(wgsOnlyPath))
        self.check_report(wgsOnlyPath, '578db31612ca2e32a6d15fc90654e01b')
        depth80XPath = os.path.join(outDir, 'djerba_80x_test.html')
        html_renderer(wgs_only=False, failed=False, log_level=logging.ERROR).run(reportDir, depth80XPath, target_coverage=80)
        self.assertTrue(os.path.exists(depth80XPath))
        self.check_report(depth80XPath, 'ef4e734835270238df9ec321aa062d89')
        wgsOnlyDepth80XPath = os.path.join(outDir, 'djerba_80x_wgs_only_test.html')
        html_renderer(wgs_only=True, failed=False, log_level=logging.ERROR).run(reportDir, wgsOnlyDepth80XPath, target_coverage=80)
        self.assertTrue(os.path.exists(wgsOnlyDepth80XPath))
        self.check_report(wgsOnlyDepth80XPath, 'e01a6fbf2e6e8f7a9ad209b2c820defe')

    def test_pdf(self):
        in_path = os.path.join(self.sup_dir, 'djerba_test.html')
        out_dir = self.tmp_dir
        out_path = os.path.join(out_dir, 'djerba_test.pdf')
        footer_text = 'PANX_1249_TEST'
        test_renderer = pdf_renderer()
        test_renderer.run(in_path, out_path, footer_text)
        # TODO check file contents; need to omit the report date etc.
        self.assertTrue(os.path.exists(out_path))

    def test_script(self):
        """Test the HTML2PDF script"""
        html_path = os.path.join(self.data_dir, 'example_page.html')
        pdf_path = os.path.join(self.tmp_dir, 'example_doc.pdf')
        cmd = [
            "html2pdf.py",
            "--html", html_path,
            "--pdf", pdf_path
        ]
        result = self.run_command(cmd)
        self.assertTrue(os.path.exists(pdf_path))
        # Compare file contents; timestamps will differ. TODO Make this more Pythonic.
        result = subprocess.run("cat {0} | grep -av CreationDate | md5sum | cut -f 1 -d ' '".format(pdf_path), shell=True, capture_output=True)
        self.assertEqual(str(result.stdout, encoding=constants.TEXT_ENCODING).strip(), '8213bfad2518570c26c9baef746b0b22')

class TestReport(TestBase):

    def test_parser(self):
        report_dir = os.path.join(self.sup_dir, 'report_example')
        parser = report_directory_parser(report_dir)
        summary = parser.get_summary()
        expected_path = os.path.join(self.sup_dir, 'expected_summary.json.gz')
        with gzip.open(expected_path) as expected_file:
            expected = json.loads(expected_file.read())
        self.assertEqual(summary, expected)

class TestSequenzaReader(TestBase):

    def setUp(self):
        super().setUp()
        self.zip_path = os.path.join(self.sup_dir, 'PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip')
        self.expected_gamma_id = (400, constants.SEQUENZA_PRIMARY_SOLUTION)

    def test_gamma_script(self):
        """Test the command-line script to find gamma"""
        json_path = os.path.join(self.tmp_dir, 'sequenza_gamma.json')
        cmd = [
            "sequenza_explorer.py",
            "read",
            "--in", self.zip_path,
            "--json", json_path,
            "--gamma-selection",
            "--purity-ploidy",
            "--summary"
        ]
        result = self.run_command(cmd)
        with open(os.path.join(self.data_dir, 'expected_sequenza.txt'), 'rt') as in_file:
            expected_text = in_file.read()
        with open(os.path.join(self.tmp_dir, 'script.txt') , 'w') as out_file:
            out_file.write(result.stdout)
        self.assertEqual(result.stdout, expected_text)
        expected_json = os.path.join(self.data_dir, 'expected_sequenza.json')
        with open(expected_json, 'rt') as exp_file, open(json_path, 'rt') as out_file:
            output = json.loads(out_file.read())
            expected = json.loads(exp_file.read())
            self.assertEqual(output, expected)

    def test_locator_script(self):
        """Test locator mode of the script"""
        cmd = [
            "sequenza_explorer.py",
            "locate",
            "--file-provenance", self.provenance,
            "--donor", self.donor,
            "--study", self.project
        ]
        result = self.run_command(cmd)
        expected_text = "/oicr/data/archive/seqware/seqware_analysis_12/hsqwprod/seqware-results/sequenza_2.1/21562306/PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip\n"
        self.assertEqual(result.stdout, expected_text)

    def test_purity_ploidy(self):
        reader = sequenza_reader(self.zip_path, log_level=logging.CRITICAL)
        self.assertEqual(reader.get_purity(), 0.6)
        self.assertEqual(reader.get_ploidy(), 3.1)
        expected_segments = {
            (100, '_primary_'): 4356,
            (100, 'sol2_0.59'): 4356,
            (1000, 'sol3_0.42'): 245,
            (1000, 'sol4_0.73'): 245,
            (1000, '_primary_'): 245,
            (1000, 'sol2_0.49'): 245,
            (1250, 'sol3_0.42'): 165,
            (1250, 'sol4_0.73'): 165,
            (1250, 'sol5_0.4'): 165,
            (1250, '_primary_'): 165,
            (1250, 'sol2_0.49'): 165,
            (1500, 'sol2_0.48'): 123,
            (1500, 'sol3_0.42'): 123,
            (1500, 'sol5_0.4'): 123,
            (1500, '_primary_'): 123,
            (1500, 'sol4_0.72'): 123,
            (200, 'sol2_0.24'): 1955,
            (200, '_primary_'): 1955,
            (200, 'sol3_0.31'): 1955,
            (2000, 'sol2_0.42'): 84,
            (2000, 'sol6_0.39'): 84,
            (2000, 'sol3_0.48'): 84,
            (2000, '_primary_'): 84,
            (2000, 'sol4_1'): 84,
            (2000, 'sol5_0.72'): 84,
            (300, 'sol4_0.43'): 1170,
            (300, 'sol2_0.32'): 1170,
            (300, 'sol3_0.24'): 1170,
            (300, '_primary_'): 1170,
            (400, 'sol3_0.43'): 839,
            (400, '_primary_'): 839,
            (400, 'sol4_1'): 839,
            (400, 'sol2_0.44'): 839,
            (400, 'sol5_0.39'): 839,
            (50, '_primary_'): 8669,
            (500, 'sol2_0.48'): 622,
            (500, 'sol3_0.42'): 622,
            (500, '_primary_'): 622,
            (500, 'sol4_0.39'): 622,
            (600, 'sol2_0.48'): 471,
            (600, 'sol3_0.42'): 471,
            (600, 'sol4_0.73'): 471,
            (600, '_primary_'): 471,
            (700, 'sol2_0.48'): 407,
            (700, 'sol3_0.42'): 407,
            (700, 'sol4_0.73'): 407,
            (700, '_primary_'): 407,
            (800, 'sol3_0.42'): 337,
            (800, 'sol4_0.73'): 337,
            (800, '_primary_'): 337,
            (800, 'sol2_0.49'): 337,
            (900, 'sol3_0.42'): 284,
            (900, 'sol4_0.73'): 284,
            (900, '_primary_'): 284,
            (900, 'sol2_0.49'): 284
        }
        self.assertEqual(reader.get_segment_counts(), expected_segments)
        self.assertEqual(reader.get_default_gamma_id(), self.expected_gamma_id)
        # test with alternate gamma
        self.assertEqual(reader.get_purity(gamma=50), 0.56)
        self.assertEqual(reader.get_ploidy(gamma=50), 3.2)
        # test with nonexistent gamma
        with self.assertRaises(SequenzaError):
            reader.get_purity(gamma=999999)
        with self.assertRaises(SequenzaError):
            reader.get_ploidy(gamma=999999)

    def test_seg_file(self):
        reader = sequenza_reader(self.zip_path, log_level=logging.CRITICAL)
        seg_path = reader.extract_seg_file(self.tmp_dir)
        self.assertEqual(
            seg_path,
            os.path.join(self.tmp_dir, 'gammas/400/PANX_1249_Lv_M_WG_100-PM-013_LCM5_Total_CN.seg')
        )
        self.assertEqual(self.getMD5(seg_path), '25b0e3c01fe77a28b24cff46081cfb1b')
        seg_path = reader.extract_seg_file(self.tmp_dir, gamma=1000)
        self.assertEqual(
            seg_path,
            os.path.join(self.tmp_dir, 'gammas/1000/PANX_1249_Lv_M_WG_100-PM-013_LCM5_Total_CN.seg')
        )
        self.assertEqual(self.getMD5(seg_path), '5d433e47431029219b6922fba63a8fcf')
        with self.assertRaises(SequenzaError):
            reader.extract_seg_file(self.tmp_dir, gamma=999999)

class TestSetup(TestBase):

    class mock_setup_args:
        """Use instead of argparse to store params for testing"""

        def __init__(self, base, name):
            self.base = base
            self.name = name
            self.subparser_name = constants.SETUP
            self.wgs_only = False
            self.failed = False
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_setup(self):
        out_dir = self.tmp_dir
        name = 'PANX_1249'
        args = self.mock_setup_args(out_dir, name)
        main(args).run()
        work_dir = os.path.join(out_dir, name)
        report_dir = os.path.join(work_dir, 'report')
        config_path = os.path.join(work_dir, 'config.ini')
        for output in (work_dir, report_dir, config_path):
            self.assertTrue(os.path.exists(output))

class TestValidator(TestBase):

    def test_config_validator(self):
        config_user = configparser.ConfigParser()
        config_user.read(self.config_user)
        config_full = configparser.ConfigParser()
        config_full.read(self.config_full)
        validator = config_validator(wgs_only=False, failed=False, log_level=logging.ERROR)
        self.assertTrue(validator.validate_minimal(config_user))
        self.assertTrue(validator.validate_full(config_full))
        # minimal config will fail the validate_full check
        validator_critical = config_validator(wgs_only=False, failed=False, log_level=logging.CRITICAL)
        with self.assertRaises(DjerbaConfigError):
            self.assertTrue(validator_critical.validate_full(config_user))

class TestWrapper(TestBase):

    def test_default(self):
        config = configparser.ConfigParser()
        config.read(self.config_full)
        out_dir = self.tmp_dir
        test_wrapper = r_script_wrapper(config, report_dir=out_dir, wgs_only=False)
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)

    def test_wgs_only(self):
        config = configparser.ConfigParser()
        config.read(self.config_full_wgs_only)
        out_dir = self.tmp_dir
        test_wrapper = r_script_wrapper(config, report_dir=out_dir, wgs_only=True)
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)


if __name__ == '__main__':
    unittest.main()
