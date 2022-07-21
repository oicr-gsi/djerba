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
from shutil import copy
from string import Template

import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.benchmark import benchmarker
from djerba.configure import configurer, log_r_cutoff_finder
from djerba.extract.extractor import extractor
from djerba.extract.r_script_wrapper import r_script_wrapper
from djerba.lister import lister
from djerba.main import main
from djerba.mavis import mavis_runner
from djerba.render.archiver import archiver
from djerba.render.render import html_renderer, pdf_renderer
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
            self.config_full_wgs_only,
            self.config_full_reduced_maf_1,
            self.config_full_reduced_maf_2,
            self.config_full_reduced_maf_wgs_only,
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
                'config_full_wgs_only.ini',
                'config_full_reduced_maf_1.ini',
                'config_full_reduced_maf_2.ini',
                'config_full_reduced_maf_wgs_only.ini'
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
        json_path = os.path.join(self.sup_dir, 'report_json', 'WGTS', 'djerba_report.json')
        archive_path = archiver().run(json_path, out_dir, 'test_ID')
        self.assertTrue(os.path.exists(archive_path))
        # contents of file are dependent on local paths
        with open(archive_path) as archive_file:
            data = json.loads(archive_file.read())
        self.assertEqual(len(data['report']), 20)
        self.assertEqual(len(data['supplementary']['config']), 3)

class TestConfigure(TestBase):

    def run_config_test(self, user_config, wgs_only, failed, expected_lines):
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(user_config)
        config['settings']['provenance'] = self.provenance
        test_configurer = configurer(config, wgs_only, failed)
        out_dir = self.tmp_dir
        out_path = os.path.join(out_dir, 'config_test_output.ini')
        test_configurer.run(out_path)
        # TODO check contents of output path; need to account for supplementary data location
        self.assertTrue(os.path.exists(out_path))
        with open(out_path) as out_file:
            lines = len(out_file.readlines())
        self.assertEqual(lines, expected_lines) # unlike archive, configParser puts a blank line at the end of the file

    def test_default(self):
        self.run_config_test(self.config_user, False, False, 52)

    def test_default_fail(self):
        self.run_config_test(self.config_user_failed, False, True, 42)

    def test_wgs_only(self):
        self.run_config_test(self.config_user_wgs_only, True, False, 50)

    def test_wgs_only_fail(self):
        self.run_config_test(self.config_user_wgs_only_failed, True, True, 42)


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
    # instead, copy in expected R script outputs as needed
    # Extractor without R script has two basic operations:
    # - write clinical data & genomic summary
    # - collate report directory contents and write JSON

    AUTHOR = 'Test Author'

    RSCRIPT_OUTPUTS_WGS_ONLY = [
            'data_CNA_oncoKBgenes_nonDiploid_annotated.txt',
            'data_CNA_oncoKBgenes_nonDiploid.txt',
            'data_CNA.txt',
            'data_expression_percentile_comparison.txt',
            'data_expression_percentile_tcga.txt',
            'data_expression_zscores_comparison.txt',
            'data_expression_zscores_tcga.txt',
            'data_log2CNA.txt',
            'data_mutations_extended_oncogenic.txt',
            'data_mutations_extended.txt',
            'data_segments.txt',
            'sequenza_meta.txt',
    ]
    # md5 sums of files in failed output
    STATIC_MD5_FAILED = {
        'data_clinical.txt': 'ec0868407eeaf100dbbbdbeaed6f1774',
        'genomic_summary.txt': '5a2f6e61fdf0f109ac3d1bcc4bb3ca71',
        'djerba_report.json': 'c0202e4d8dd7bacd80f37658b9c09a88'
    }
    VARYING_OUTPUT = [
        'tmb.svg',
        'vaf.svg',
        'djerba_report.json'
    ]

    def check_json(self, found_path, expected_path):
        with open(found_path) as in_file:
            data_found = json.loads(in_file.read())
        with open(expected_path) as in_file:
            data_expected = json.loads(in_file.read())
        # plot paths/contents are not fixed
        for key in ['oicr_logo', 'tmb_plot', 'vaf_plot']:
            del data_found['report'][key]
            del data_expected['report'][key]
        # do not check supplementary data
        del data_found['supplementary']
        del data_expected['supplementary']
        # replace djerba version with a placeholder
        data_found['report']['djerba_version'] = 'PLACEHOLDER'
        self.maxDiff = None
        self.assertEqual(data_found, data_expected)

    def check_outputs_md5(self, out_dir, outputs):
        for filename in outputs.keys():
            output_path = os.path.join(out_dir, filename)
            self.assertTrue(os.path.exists(output_path), filename+' exists')
            self.assertEqual(self.getMD5(output_path), outputs[filename])

    def get_static_md5_passed(self):
        static_md5_passed = self.STATIC_MD5_FAILED.copy()
        del static_md5_passed['djerba_report.json']
        return static_md5_passed

    def run_extractor(self, user_config, out_dir, wgs_only, failed, depth):
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(user_config)
        test_extractor = extractor(config, out_dir, self.AUTHOR, wgs_only, failed, depth, log_level=logging.ERROR)
        # do not test R script here; see TestWrapper
        test_extractor.run(r_script=False)

    def test_failed_mode(self):
        # test failed mode; does not require R script output
        out_dir = os.path.join(self.tmp_dir, 'failed')
        os.mkdir(out_dir)
        self.run_extractor(self.config_full, out_dir, False, True, 80)
        self.check_outputs_md5(out_dir, self.STATIC_MD5_FAILED)

    def test_wgts_mode(self):
        out_dir = os.path.join(self.tmp_dir, 'WGTS')
        os.mkdir(out_dir)
        rscript_outputs = self.RSCRIPT_OUTPUTS_WGS_ONLY.copy()
        rscript_outputs.extend([
            'data_fusions_new_delimiter.txt',
            'data_fusions_oncokb_annotated.txt',
            'data_fusions.txt'
        ])
        for file_name in rscript_outputs:
            file_path = os.path.join(self.sup_dir, 'report_example', file_name)
            copy(file_path, out_dir)
        self.run_extractor(self.config_full, out_dir, False, False, 80)
        self.check_outputs_md5(out_dir, self.get_static_md5_passed())
        for name in self.VARYING_OUTPUT:
            self.assertTrue(os.path.exists(os.path.join(out_dir, name)), name+' exists')
        ref_dir = os.path.join(self.sup_dir, 'report_json', 'WGTS')
        found = os.path.join(out_dir, 'djerba_report.json')
        expected = os.path.join(ref_dir, 'djerba_report.json')
        self.check_json(found, expected)

    def test_wgs_only_mode(self):
        out_dir = os.path.join(self.tmp_dir, 'WGS_only')
        os.mkdir(out_dir)
        for file_name in self.RSCRIPT_OUTPUTS_WGS_ONLY:
            file_path = os.path.join(self.sup_dir, 'report_example', file_name)
            copy(file_path, out_dir)
        self.run_extractor(self.config_full, out_dir, True, False, 80)
        self.check_outputs_md5(out_dir, self.get_static_md5_passed())
        for name in self.VARYING_OUTPUT:
            self.assertTrue(os.path.exists(os.path.join(out_dir, name)))
        ref_dir = os.path.join(self.sup_dir, 'report_json', 'WGS_only')
        found = os.path.join(out_dir, 'djerba_report.json')
        expected = os.path.join(ref_dir, 'djerba_report.json')
        self.check_json(found, expected)

    def test_cancer_type_description(self):
        # test extraction of the cancer type description; see GCGI-333
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(self.config_full)
        out_dir = self.tmp_dir
        wgs_only = False
        failed = False
        depth = 80
        test_extractor = extractor(config, out_dir, self.AUTHOR, wgs_only, failed, depth, log_level=logging.ERROR)
        desc = test_extractor.get_description()
        expected = [
            {'cancer_type': 'Pancreas', 'cancer_description': 'Pancreatic Adenocarcinoma'},
            {'cancer_type': 'Uterus', 'cancer_description': 'Epithelioid Trophoblastic Tumor'},
            {'cancer_type': 'UNKNOWN', 'cancer_description': 'UNKNOWN'},
        ]
        self.assertEqual(test_extractor.get_description(), expected[0])
        config[ini.INPUTS][ini.ONCOTREE_CODE] = 'ETT'
        self.assertEqual(test_extractor.get_description(), expected[1])
        config[ini.INPUTS][ini.ONCOTREE_CODE] = 'FOO'
        self.assertEqual(test_extractor.get_description(), expected[2])

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

class TestJsonScripts(TestBase):

    def test_update(self):
        update_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do '+\
                      'eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        update_path = os.path.join(self.tmp_dir, 'lorem.txt')
        with open(update_path, 'w') as out_file:
            out_file.write(update_text)
        input_path = os.path.join(self.sup_dir, 'report_json', 'WGTS', 'djerba_report.json')
        output_path = os.path.join(self.tmp_dir, 'updated_djerba_report.json')
        cmd = [
            'update_genomic_summary.py',
            '--in', input_path,
            '--summary', update_path,
            '--out', output_path
        ]
        self.run_command(cmd)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path) as output_file:
            data = json.loads(output_file.read())
        self.assertEqual(data['report']['genomic_summary'], update_text)

    def test_view(self):
        input_path = os.path.join(self.sup_dir, 'report_json', 'WGTS', 'djerba_report.json')
        output_path = os.path.join(self.tmp_dir, 'viewed_djerba_report.json')
        cmd = [
            'view_json.py',
            '--in', input_path,
            '--out', output_path
        ]
        self.run_command(cmd)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path) as output_file:
            data = json.loads(output_file.read())
        for key in ['oicr_logo', 'tmb_plot', 'vaf_plot']:
            self.assertEqual(data['report'][key], 'REDACTED')
        # spot check on a non-redacted result
        self.assertEqual(data['report']['oncogenic_somatic_CNVs']['Total variants'], 40)

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
        if not os.path.exists(work_dir):
            os.mkdir(work_dir)
        args = self.mock_args(ini_path, config_path, html_path, work_dir)
        main(args).run()
        self.assertTrue(os.path.exists(html_path))
        pdf_path = os.path.join(work_dir, '100-PM-013_LCM5-v1_report.pdf')
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
        args_path = os.path.join(self.sup_dir, 'report_json', 'WGTS', 'djerba_report.json')
        out_path = os.path.join(self.tmp_dir, 'djerba_test_wgts.html')
        html_renderer().run(args_path, out_path, False)
        self.check_report(out_path, 'b1927827966a710dd35d79624a2d5974')
        args_path = os.path.join(self.sup_dir, 'report_json', 'WGS_only', 'djerba_report.json')
        out_path = os.path.join(self.tmp_dir, 'djerba_test_wgs_only.html')
        html_renderer().run(args_path, out_path, False)
        self.check_report(out_path, '8f04976a32afe28bcacb13ad7b44674a')
        args_path = os.path.join(self.sup_dir, 'report_json', 'failed', 'djerba_report.json')
        out_path = os.path.join(self.tmp_dir, 'djerba_test_failed.html')
        html_renderer().run(args_path, out_path, False)
        self.check_report(out_path, 'eec0196e171c66cae1de061d85bcb677')

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

    def test_old_maf(self):
        config = configparser.ConfigParser()
        config.read(self.config_full_reduced_maf_1)
        out_dir = self.tmp_dir
        test_wrapper = r_script_wrapper(config, report_dir=out_dir, wgs_only=False)
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)

    def test_new_maf(self):
        config = configparser.ConfigParser()
        config.read(self.config_full_reduced_maf_2)
        out_dir = self.tmp_dir
        test_wrapper = r_script_wrapper(config, report_dir=out_dir, wgs_only=False)
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)

    def test_wgs_only(self):
        config = configparser.ConfigParser()
        config.read(self.config_full_reduced_maf_wgs_only)
        out_dir = self.tmp_dir
        test_wrapper = r_script_wrapper(config, report_dir=out_dir, wgs_only=True)
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)


if __name__ == '__main__':
    unittest.main()
