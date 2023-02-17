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
import requests
import posixpath
from shutil import copy
from string import Template

import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.configure import configurer, log_r_cutoff_finder
from djerba.extract.extractor import extractor
from djerba.extract.oncokb.annotator import oncokb_annotator
from djerba.extract.oncokb.cache import oncokb_cache, oncokb_cache_params
from djerba.extract.r_script_wrapper import r_script_wrapper
from djerba.lister import lister
from djerba.main import main
from djerba.mavis import mavis_runner
from djerba.render.archiver import archiver
from djerba.render.render import html_renderer, pdf_renderer
from djerba.sequenza import sequenza_reader, SequenzaError
from djerba.util.provenance_reader import InsufficientSampleNamesError, UnknownTumorNormalIDError
from djerba.util.validator import config_validator, DjerbaConfigError

class TestBase(unittest.TestCase):

    def getMD5(self, inputPath):
        md5 = hashlib.md5()
        with open(inputPath, 'rb') as f:
            md5.update(f.read())
        return md5.hexdigest()

    def gunzip_and_getMD5(self, inputPath):
        md5 = hashlib.md5()
        with gzip.open(inputPath, 'rb') as f:
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
        bench_dir_var = 'DJERBA_GSICAPBENCH_DATA'
        self.sup_dir = os.environ.get(sup_dir_var)
        self.bench_dir = os.environ.get(bench_dir_var)
        if not (self.sup_dir):
            raise RuntimeError('Need to specify environment variable {0}'.format(sup_dir_var))
        elif not os.path.isdir(self.sup_dir):
            raise OSError("Supplementary directory path '{0}' is not a directory".format(self.sup_dir))
        if not (self.bench_dir):
            raise RuntimeError('Need to specify environment variable {0}'.format(bench_dir_var))
        elif not os.path.isdir(self.bench_dir):
            raise OSError("GSICAPBENCH directory path '{0}' is not a directory".format(self.bench_dir))
        self.provenance = os.path.join(self.sup_dir, 'pass01_panx_provenance.original.tsv.gz')
        self.provenance_vnwgts = os.path.join(self.sup_dir, 'provenance_VNWGTS_0329.tsv.gz')
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
            self.config_user_vnwgts,
            self.config_user_vnwgts_broken_1,
            self.config_user_vnwgts_broken_2,
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
                'config_user_vnwgts.ini',
                'config_user_vnwgts_broken_1.ini',
                'config_user_vnwgts_broken_2.ini',
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
        json_path = os.path.join(self.sup_dir, 'report_json', 'WGTS', 'djerba_report.json')
        archive_status, report_id = archiver().run(json_path)
        self.assertTrue(archive_status)
        with open(json_path) as json_file:
            data = json.loads(json_file.read())
            report_id2 = data["report"]["patient_info"]["Report ID"]
            archive_url = data["supplementary"]["config"]["settings"]["archive_url"]
            archive_name = data["supplementary"]["config"]["settings"]["archive_name"]
        self.assertEqual(report_id, report_id2)
        url_id = posixpath.join(archive_url, archive_name, report_id)
        get = requests.get(url_id)
        self.assertEqual(get.status_code, 200)
        get = json.loads(get.text)
        self.assertEqual(report_id, get["report"]["patient_info"]["Report ID"])
        self.assertEqual(get["_id"], get["report"]["patient_info"]["Report ID"])
        rm = requests.delete(url_id+'?rev='+get["_rev"])
        self.assertEqual(rm.status_code, 200)
        self.assertEqual(len(data['report']), 25)  
        self.assertEqual(len(data['supplementary']['config']), 3)

class TestConfigure(TestBase):

    def run_config_test(self, user_config, wgs_only, failed, expected_lines, provenance):
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(user_config)
        config['settings']['provenance'] = provenance
        test_configurer = configurer(config, wgs_only, failed)
        out_dir = self.tmp_dir
        out_path = os.path.join(out_dir, 'config_test_output.ini')
        test_configurer.run(out_path)
        # TODO check contents of output path; need to account for supplementary data location
        self.assertTrue(os.path.exists(out_path))
        with open(out_path) as out_file:
            lines = len(out_file.readlines())
        self.assertEqual(lines, expected_lines) # unlike archive, configParser puts a blank line at the end of the file

    def run_config_broken(self, user_config, provenance):
        # no assertions; run is intended to fail
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(user_config)
        config['settings']['provenance'] = provenance
        test_configurer = configurer(config, wgs_only=False, failed=False, log_level=logging.CRITICAL)
        out_dir = self.tmp_dir
        out_path = os.path.join(out_dir, 'config_test_output.ini')
        test_configurer.run(out_path)

    def test_default(self):
        self.run_config_test(self.config_user, False, False, 62, self.provenance)

    def test_default_fail(self):
        self.run_config_test(self.config_user_failed, False, True, 51, self.provenance)

    def test_wgs_only(self):
        self.run_config_test(self.config_user_wgs_only, True, False, 60, self.provenance)

    def test_wgs_only_fail(self):
        self.run_config_test(self.config_user_wgs_only_failed, True, True, 51, self.provenance)

    def test_vnwgts(self):
        self.run_config_test(self.config_user_vnwgts, False, False, 62, self.provenance_vnwgts)

    def test_vnwgts_broken(self):
        # test failure modes of sample input
        with self.assertRaises(InsufficientSampleNamesError):
            self.run_config_broken(self.config_user_vnwgts_broken_1, self.provenance_vnwgts)
        with self.assertRaises(UnknownTumorNormalIDError):
            self.run_config_broken(self.config_user_vnwgts_broken_2, self.provenance_vnwgts)

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
        'data_CNA_oncoKBgenes_ARatio.txt',
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
        'aratio_segments.txt',
        'sequenza_meta.txt',
        'msi.txt'
    ]
    # md5 sums of files in failed output
    STATIC_MD5 = {
        'data_clinical.txt': 'ec0868407eeaf100dbbbdbeaed6f1774',
        'genomic_summary.txt': 'f53692a7bf5879bb6e5b4f26047d7297',
        'technical_notes.txt': '7caedb48f3360f33937cb047579633fd'
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
        for key in ['oicr_logo', 'cnv_plot', 'pga_plot', 'tmb_plot', 'vaf_plot']:
            del data_found['report'][key]
            del data_expected['report'][key]
        for biomarker in range(0,len(data_found['report']['genomic_biomarkers']['Body'])):
            del data_found['report']['genomic_biomarkers']['Body'][biomarker]['Genomic biomarker plot']
        for biomarker in range(0,len(data_expected['report']['genomic_biomarkers']['Body'])):
            del data_expected['report']['genomic_biomarkers']['Body'][biomarker]['Genomic biomarker plot']
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

    def run_extractor(self, user_config, out_dir, wgs_only, failed, depth):
        config = configparser.ConfigParser()
        config.read(self.default_ini)
        config.read(user_config)
        test_extractor = extractor(config, out_dir, self.AUTHOR, wgs_only, failed, depth, oncokb_cache_params(), log_level=logging.ERROR)
        # do not test R script here; see TestWrapper
        test_extractor.run(r_script=False)

    def test_failed_mode(self):
        # test failed mode; does not require R script output
        out_dir = os.path.join(self.tmp_dir, 'failed')
        os.mkdir(out_dir)
        self.run_extractor(self.config_full, out_dir, False, True, 80)
        self.check_outputs_md5(out_dir, self.STATIC_MD5)
        with open(os.path.join(out_dir, 'djerba_report.json')) as in_file:
            data_found = json.loads(in_file.read())
            data_found['report']['djerba_version'] = 'PLACEHOLDER'
            del data_found['supplementary'] # do not test supplementary data
            data = json.dumps(data_found)
            self.assertEqual(hashlib.md5(data.encode(encoding=constants.TEXT_ENCODING)).hexdigest(), '37bace335089f94b92e69c44e9ba64dc')

    def test_wgts_mode(self):
        out_dir = os.path.join(self.tmp_dir, 'WGTS')
        os.mkdir(out_dir)
        rscript_outputs = self.RSCRIPT_OUTPUTS_WGS_ONLY.copy()
        rscript_outputs.extend([
            'data_fusions_new_delimiter.txt',
            'data_fusions_oncokb_annotated.txt',
            'data_fusions.txt',
        ])
        for file_name in rscript_outputs:
            file_path = os.path.join(self.sup_dir, 'report_example', file_name)
            copy(file_path, out_dir)
        self.run_extractor(self.config_full, out_dir, False, False, 80)
        self.check_outputs_md5(out_dir, self.STATIC_MD5)
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
        self.check_outputs_md5(out_dir, self.STATIC_MD5)
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
        test_extractor = extractor(config, out_dir, self.AUTHOR, wgs_only, failed, depth, oncokb_cache_params(), log_level=logging.ERROR)
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
            # sample names
            self.wgn = None
            self.wgt = None
            self.wtt = None
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
        
    def test_update_notes(self):
        update_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do '+\
                      'eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        update_path = os.path.join(self.tmp_dir, 'lorem.txt')
        with open(update_path, 'w') as out_file:
            out_file.write(update_text)
        input_path = os.path.join(self.sup_dir, 'report_json', 'WGTS', 'djerba_report.json')
        output_path = os.path.join(self.tmp_dir, 'updated_djerba_report.json')
        cmd = [
            'update_technical_notes.py',
            '--in', input_path,
            '--notes', update_path,
            '--out', output_path
        ]
        self.run_command(cmd)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path) as output_file:
            data = json.loads(output_file.read())
        self.assertEqual(data['report']['technical_notes'], update_text)

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
            self.no_cleanup = False
            self.wgs_only = False
            # oncokb cache
            self.cache_dir = None
            self.apply_cache = True # Use cache for speed; test OncoKB usage elsewhere
            self.update_cache = False
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
            # sample names
            self.wgn = None
            self.wgt = None
            self.wtt = None
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

class TestOncokbAnnotator(TestBase):

    # Test for online OncoKB annotation with reduced MAF input

    def test_annotator(self):
        input_dir = os.path.join(self.sup_dir, 'oncokb')
        out_dir = self.tmp_dir
        annotator = oncokb_annotator('100-PM-047_LCM1_4', 'PAAD', out_dir)
        cna = os.path.join(input_dir, 'data_CNA_oncoKBgenes_nonDiploid.txt')
        fusion = os.path.join(input_dir, 'data_fusions_oncokb.txt')
        maf = os.path.join(input_dir, 'raw_maf_100.tsv')
        for input_file in [cna, fusion]:
            copy(input_file, out_dir)
        annotator.annotate_cna()
        cna_out = os.path.join(out_dir, 'data_CNA_oncoKBgenes_nonDiploid_annotated.txt')
        self.assertTrue(os.path.exists(cna_out))
        self.assertEqual(self.getMD5(cna_out), 'da428449a3145cbf9a2f7f1bdf45786d')
        annotator.annotate_fusion()
        fusion_out = os.path.join(out_dir, 'data_fusions_oncokb_annotated.txt')
        self.assertTrue(os.path.exists(fusion_out))
        self.assertEqual(self.getMD5(fusion_out), '570b4ce1fe08e2323b1e84fcb5b2c58c')
        annotator.annotate_maf(maf)
        maf_out = os.path.join(out_dir, 'annotated_maf.tsv')
        self.assertTrue(os.path.exists(maf_out))
        self.assertEqual(self.getMD5(maf_out), '0d7178017054f9b60f48044b58d907e4')

class TestOncokbCache(TestBase):

    # test if we can do a round trip:
    # - make cache from annotated file
    # - annotate a raw file from the cache
    # - check that cache-annotated and original annotated files are the same

    def test_cna(self):
        input_dir = os.path.join(self.sup_dir, 'oncokb')
        annotated_cna = os.path.join(input_dir, 'data_CNA_oncoKBgenes_nonDiploid_annotated.txt')
        raw_cna = os.path.join(input_dir, 'data_CNA_oncoKBgenes_nonDiploid.txt')
        out_dir = self.tmp_dir
        cache = oncokb_cache(out_dir)
        cache_out_path = cache.write_cna_cache(annotated_cna)
        self.assertTrue(os.path.exists(cache_out_path))
        with open(cache_out_path) as cache_file:
            cache_data = json.loads(cache_file.read())
        expected = ["True", "True", "True", "Likely Loss-of-function", "25736321;27558455;25521327",
                    "Likely Oncogenic", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
                    "", "", "", "", "", ""]
        found = cache_data["TGFBR2"]["Deletion"]
        self.assertEqual(expected, found)
        cna_out_path = os.path.join(out_dir, 'annotated_cna.tsv')
        oncokb_info = os.path.join(input_dir, 'oncokb_clinical_info.txt')
        cache.annotate_cna(raw_cna, cna_out_path, oncokb_info)
        self.assertTrue(os.path.exists(cna_out_path))
        self.assertEqual(self.getMD5(cna_out_path), self.getMD5(annotated_cna))

    def test_fusion(self):
        input_dir = os.path.join(self.sup_dir, 'oncokb')
        annotated_fusion = os.path.join(input_dir, 'data_fusions_oncokb_annotated.txt')
        raw_fusion = os.path.join(input_dir, 'data_fusions_oncokb.txt')
        out_dir = self.tmp_dir
        cache = oncokb_cache(out_dir)
        cache_out_path = cache.write_fusion_cache(annotated_fusion)
        self.assertTrue(os.path.exists(cache_out_path))
        with open(cache_out_path) as cache_file:
            cache_data = json.loads(cache_file.read())
        expected = ['True', 'True', 'False', 'Likely Loss-of-function', '21174539',
                    'Likely Oncogenic', '', '', '', '', '', '', '', '', '', '', '', '', '',
                    '', '', '', '', '', '', '', '']
        found = cache_data['RUNX1-SHROOM2']
        self.assertEqual(expected, found)
        fusion_out_path = os.path.join(out_dir, 'annotated_fusion.tsv')
        cache.annotate_fusion(raw_fusion, fusion_out_path)
        self.assertTrue(os.path.exists(fusion_out_path))
        self.assertEqual(self.getMD5(fusion_out_path), self.getMD5(annotated_fusion))

    def test_maf(self):
        input_dir = os.path.join(self.sup_dir, 'oncokb')
        annotated_maf = os.path.join(input_dir, 'annotated_maf.tsv.gz')
        raw_maf = os.path.join(input_dir, 'raw_maf.tsv.gz')
        out_dir = self.tmp_dir
        cache = oncokb_cache(out_dir)
        cache_out_path = cache.write_maf_cache(annotated_maf)
        self.assertTrue(os.path.exists(cache_out_path))
        with open(cache_out_path) as cache_file:
            cache_data = json.loads(cache_file.read())
        expected = ["True", "True", "False", "Likely Loss-of-function",
                    "22072542;22588899;21817013;24117486", "Likely Oncogenic", "", "", "", "",
                    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        found = cache_data.get('51f977c04bfb0e703a3b42bb451a782445f9b9f9362dbd38db5408d95553414b')
        self.assertEqual(expected, found)
        maf_out_path = os.path.join(out_dir, 'annotated_maf.tsv')
        cache.annotate_maf(raw_maf, maf_out_path)
        self.assertTrue(os.path.exists(maf_out_path))
        self.assertEqual(self.getMD5(maf_out_path), self.gunzip_and_getMD5(annotated_maf))

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
        self.check_report(out_path, 'cd839d15b7b9fb6218811997c70e9a28')
        args_path = os.path.join(self.sup_dir, 'report_json', 'WGS_only', 'djerba_report.json')
        out_path = os.path.join(self.tmp_dir, 'djerba_test_wgs_only.html')
        html_renderer().run(args_path, out_path, False)
        self.check_report(out_path, '31166a33b4e3818c6431b96986f8a0a7')
        args_path = os.path.join(self.sup_dir, 'report_json', 'failed', 'djerba_report.json')
        out_path = os.path.join(self.tmp_dir, 'djerba_test_failed.html')
        html_renderer().run(args_path, out_path, False)
        self.check_report(out_path, 'eca17184609ebf9f7a7264533c5c52e2')

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
        self.assertEqual(str(result.stdout, encoding=constants.TEXT_ENCODING).strip(), 'dea1aeef66e5c0d22242a7d38123ffbc')

class TestSequenzaReader(TestBase):

    def setUp(self):
        super().setUp()
        self.zip_path = os.path.join(self.sup_dir, 'PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip')
        self.expected_sol_id = (400, constants.SEQUENZA_PRIMARY_SOLUTION)

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
        self.maxDiff = None
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
        self.assertEqual(reader.get_default_sol_id(), self.expected_sol_id)
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
        seg_path = reader.extract_cn_seg_file(self.tmp_dir)
        self.assertEqual(
            seg_path,
            os.path.join(self.tmp_dir, 'gammas/400/PANX_1249_Lv_M_WG_100-PM-013_LCM5_Total_CN.seg')
        )
        self.assertEqual(self.getMD5(seg_path), '25b0e3c01fe77a28b24cff46081cfb1b')
        seg_path = reader.extract_cn_seg_file(self.tmp_dir, gamma=1000)
        self.assertEqual(
            seg_path,
            os.path.join(self.tmp_dir, 'gammas/1000/PANX_1249_Lv_M_WG_100-PM-013_LCM5_Total_CN.seg')
        )
        self.assertEqual(self.getMD5(seg_path), '5d433e47431029219b6922fba63a8fcf')
        with self.assertRaises(SequenzaError):
            reader.extract_cn_seg_file(self.tmp_dir, gamma=999999)

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
        test_wrapper = r_script_wrapper(config, out_dir, False, oncokb_cache_params())
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)

    def test_new_maf(self):
        config = configparser.ConfigParser()
        config.read(self.config_full_reduced_maf_2)
        out_dir = self.tmp_dir
        test_wrapper = r_script_wrapper(config, out_dir, False, oncokb_cache_params())
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)

    def test_wgs_only(self):
        config = configparser.ConfigParser()
        config.read(self.config_full_reduced_maf_wgs_only)
        out_dir = self.tmp_dir
        test_wrapper = r_script_wrapper(config, out_dir, True, oncokb_cache_params())
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)


if __name__ == '__main__':
    unittest.main()
