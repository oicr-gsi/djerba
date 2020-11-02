#! /usr/bin/env python3

import hashlib, logging, json, os, random, subprocess, tempfile, unittest

from djerba.metrics import mutation_extended_metrics
from djerba.report import report, DjerbaReportError
from djerba.sample import sample
from djerba.study import study
from djerba.utilities import constants
from djerba.config import builder, validator, DjerbaConfigError

class TestBase(unittest.TestCase):

    SCHEMA_PATH = '/.mounts/labs/gsi/modulator/sw/data/elba-config-schema-1.0.0/elba_config_schema.json' # path to Elba JSON schema
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_test_')

    def verify_checksums(self, checksums, out_dir):
        """Checksums is a dictionary: md5sum -> relative path from output directory """
        for relative_path in checksums.keys():
            out_path = os.path.join(out_dir, relative_path)
            self.assertTrue(os.path.exists(out_path), out_path+" exists")
            md5 = hashlib.md5()
            with open(out_path, 'rb') as f:
                md5.update(f.read())
            self.assertEqual(md5.hexdigest(),
                             checksums[relative_path],
                             out_path+" checksums match")

    def tearDown(self):
        self.tmp.cleanup()

class TestBuilder(TestBase):
    """Tests for Elba config builder"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_builder_test_')
        self.sample_id = "OCT-01-0472-CAP"

    def test(self):
        test_builder = builder(self.sample_id, log_level=logging.WARN)
        test_subdir = os.path.join(self.dataDir, 'from_command')
        maf_dir = '/.mounts/labs/gsiprojects/gsi/djerba/mutation_extended'
        args = [
            test_subdir, # custom_dir
            'custom_gene_annotation.tsv', # gene_tsv
            'custom_sample_annotation.tsv', # sample_tsv
            os.path.join(maf_dir, 'somatic01.maf.txt.gz'), # maf
            '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/S31285117_Regions.bed', # bed
            'blca', # cancer_type
            None, # oncokb_token
            '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/tcga_tmbs.txt', # tcga
            '/.mounts/labs/gsiprojects/gsi/cBioGSI/data/reference/ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz'
        ]
        # generate the Elba config
        config = test_builder.build(*args)
        with open(os.path.join(test_subdir, 'expected_djerba_config.json')) as expected_file:
            expected = json.loads(expected_file.read())
        # ordering of items in genetic_alterations is fixed in the builder code
        expected[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = test_subdir
        expected[constants.GENETIC_ALTERATIONS_KEY][1]['input_directory'] = maf_dir
        self.assertEqual(config, expected, "Elba config matches expected values")
        # test writing a report with the generated Elba config
        out_name = 'elba_report_config.json'
        out_dir = os.path.join(self.tmp.name, 'builder_test')
        os.mkdir(out_dir)
        elba_report = report(config, self.sample_id, log_level=logging.ERROR)
        elba_report.write_report_config(os.path.join(out_dir, out_name), force=False, strict=True)
        checksums = {out_name: '9ff34457654edf49eef4104e23680710'}
        self.verify_checksums(checksums, out_dir)

    def test_mismatched(self):
        test_builder = builder(self.sample_id, log_level=logging.WARN)
        test_subdir = os.path.join(self.dataDir, 'from_command')
        maf_dir = '/.mounts/labs/gsiprojects/gsi/djerba/mutation_extended'
        args = [
            test_subdir, # custom_dir
            'mismatched_custom_gene_annotation.tsv', # gene_tsv
            'custom_sample_annotation.tsv', # sample_tsv
            os.path.join(maf_dir, 'somatic01.maf.txt.gz'), # maf
            '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/S31285117_Regions.bed', # bed
            'blca', # cancer_type
            None, # oncokb_token
            '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/tcga_tmbs.txt', # tcga
            '/.mounts/labs/gsiprojects/gsi/cBioGSI/data/reference/ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz'
        ]
        # generate the Elba config
        config = test_builder.build(*args)
        with open(os.path.join(test_subdir, 'expected_djerba_config_mismatch.json')) as expected_file:
            expected = json.loads(expected_file.read())
        # ordering of items in genetic_alterations is fixed in the builder code
        expected[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = test_subdir
        expected[constants.GENETIC_ALTERATIONS_KEY][1]['input_directory'] = maf_dir
        self.assertEqual(config, expected, "Elba config matches expected values")
        # test writing a report with the generated Elba config
        out_name = 'elba_report_config.json'
        out_dir = os.path.join(self.tmp.name, 'builder_test_mismatch')
        os.mkdir(out_dir)
        elba_report = report(config, self.sample_id, log_level=logging.ERROR)
        elba_report.write_report_config(os.path.join(out_dir, out_name), force=False, strict=False)
        checksums = {out_name: '1c280d3ad86c03e92f67adbbf5b8c74c'}
        self.verify_checksums(checksums, out_dir)
        # writing fails in strict mode, because gene attributes are inconsistent
        args = [config, self.sample_id, logging.CRITICAL]
        elba_report_strict = report(config, self.sample_id, log_level=logging.CRITICAL)
        args = [os.path.join(out_dir, out_name), True, True] # force=True, strict=True
        self.assertRaises(DjerbaReportError, elba_report_strict.write_report_config, *args)

class TestMetrics(TestBase):
    """Tests for genetic alteration metrics"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/'
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_mx_metrics_test_')

    def test_mx_tmb(self):
        """Test the Tumor Mutation Burden metric"""
        maf_path = os.path.join(self.data_dir, 'tmb', 'somatic.maf.txt.gz')
        bed_path = os.path.join(self.data_dir, 'tmb', 'S31285117_Regions.bed')
        tcga_path = os.path.join(self.data_dir, 'tmb', 'tcga_tmbs.txt')
        cancer_type = "blca"
        with open(os.path.join(self.data_dir, 'tmb_expected.json')) as exp_file:
            expected = json.loads(exp_file.read())
        mx_metrics = mutation_extended_metrics(maf_path, bed_path, tcga_path, cancer_type)
        output = [
            mx_metrics.get_tmb(),
            mx_metrics.get_tcga_pct(),
            mx_metrics.get_cohort_pct(),
            mx_metrics.get_tcga_tmb_as_dict(),
            mx_metrics.get_cohort_tmb_as_dict(),
        ]
        for i in (0,1,2):
            # Test singleton floats
            self.assertAlmostEqual(output[i], expected[i])
        for i in (3,4):
            # Test dictionaries. JSON converts dictionary keys to strings.
            # So keys are integers for output dictionaries, strings for expected dictionaries.
            # List equality is ambiguous, so convert the key collections to sets before comparison
            self.assertEqual(set(output[i].keys()), set([int(k) for k in expected[i].keys()]))
            for key in output[i].keys():
                self.assertAlmostEqual(output[i][key], expected[i][str(key)])


class TestReport(TestBase):
    """Tests for clinical report output"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_report_test_')
        self.sample_id = 'OCT-01-0472-CAP'

    def test_custom(self):
        """Test report with custom_annotation input"""
        out_dir = os.path.join(self.tmp.name, 'test_report_custom')
        os.mkdir(out_dir)
        config_names = ['report_config_custom.json', 'report_config_custom_with_nan.json']
        report_names = ["report_config_{}.json".format(i) for i in range(len(config_names))]
        for i in range(len(config_names)):
            with open(os.path.join(self.dataDir, config_names[i])) as configFile:
                config = json.loads(configFile.read())
            # get input from the local test directory
            config[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = self.dataDir
            report_path = os.path.join(out_dir, report_names[i])
            custom_report = report(config, self.sample_id, self.SCHEMA_PATH, log_level=logging.ERROR)
            custom_report.write_report_config(report_path)
            self.assertTrue(os.path.exists(report_path), "JSON report exists")
        checksums = {
            report_names[0]: '924d017ffd6f744b37c1c6650abd6aca',
            report_names[1]: 'bf7f60aab3a144ffe112794aa2744208'
        }
        self.verify_checksums(checksums, out_dir)
        # test with incorrect sample headers in metadata
        with open(os.path.join(self.dataDir, 'report_config_custom_broken.json')) as configFile:
            config = json.loads(configFile.read())
        config[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = self.dataDir
        args = [config, self.sample_id, self.SCHEMA_PATH, logging.CRITICAL]
        self.assertRaises(ValueError, report, *args)

    def test_mx(self):
        """Test report with 'mutation extended' input"""
        report_name = 'report_mx.json'
        out_dir = os.path.join(self.tmp.name, 'test_report_mx')
        os.mkdir(out_dir)
        # can't use study_config_mx.json; djerba does not yet support custom annotation for cBioPortal
        with open(os.path.join(self.dataDir, 'report_config_mx.json')) as configFile:
            config = json.loads(configFile.read())
        # get custom config input from the local test directory
        config[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = self.dataDir
        report_path = os.path.join(out_dir, report_name)
        mx_report = report(config, self.sample_id, self.SCHEMA_PATH, log_level=logging.ERROR)
        mx_report.write_report_config(report_path)
        self.assertTrue(os.path.exists(report_path), "JSON report exists")
        checksum = {report_name: 'c37c953b63227730d4009c7a0ec56896'}
        self.verify_checksums(checksum, out_dir)
        args = [config, 'nonexistent sample', self.SCHEMA_PATH, logging.CRITICAL]
        self.assertRaises(DjerbaReportError, report, *args)


class TestScript(TestBase):
    """Tests of command-line script"""

    def setUp(self):
        super().setUp()
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.binDir =  os.path.realpath(os.path.join(self.testDir, os.pardir, 'bin'))
        self.scriptNames = ['djerba.py', 'djerba_from_command.py']

    def test_compile(self):
        """Minimal test that command-line scripts compile"""
        for scriptName in self.scriptNames:
            scriptPath = os.path.join(self.binDir, scriptName)
            with open(scriptPath, 'rb') as inFile:
                self.assertIsNotNone(
                    compile(inFile.read(), scriptName, 'exec'),
                    'Script {} compiled without error'.format(scriptName)
                )

    def test_equivalence(self):
        """
        Test that config from djerba_from_command.py produces identical output from djerba.py
        Also tests script operation on the command line in Elba mode
        """
        out_dir = os.path.join(self.tmp.name, 'test_script_equivalence')
        os.mkdir(out_dir)
        output_path_1 = os.path.join(out_dir, 'elba_config_1.json')
        output_path_2 = os.path.join(out_dir, 'elba_config_2.json')
        config_path = os.path.join(out_dir, 'djerba_config.json')
        args_1 = [
            os.path.join(self.binDir, 'djerba_from_command.py'),
            '--conf', config_path,
            '--sample-id' ,'OCT-01-0472-CAP',
            '--custom-dir', self.dataDir,
            '--elba-schema', self.SCHEMA_PATH,
            '--gene-tsv', 'custom_gene_annotation.tsv',
            '--sample-tsv', 'custom_sample_annotation.tsv',
            '--maf', '/.mounts/labs/gsiprojects/gsi/djerba/mutation_extended/somatic01.maf.txt.gz',
            '--bed', '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/S31285117_Regions.bed',
            '--cancer-type', 'blca',
            '--tcga', '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/tcga_tmbs.txt',
            '--vcf',
            '/.mounts/labs/gsiprojects/gsi/cBioGSI/data/reference/ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz',
            '--out', output_path_1
        ]
        subprocess.run(args_1)
        self.assertTrue(os.path.exists(output_path_1))
        self.assertTrue(os.path.exists(config_path))
        args_2 = [
            os.path.join(self.binDir, 'djerba.py'),
            '--config', config_path,
            '--mode', 'elba',
            '--elba-schema', self.SCHEMA_PATH,
            '--out', output_path_2
        ]
        subprocess.run(args_2)
        self.assertTrue(os.path.exists(output_path_2))
        with open(output_path_1) as file_1, open(output_path_2) as file_2:
            data_1 = json.loads(file_1.read())
            data_2 = json.loads(file_2.read())
        self.assertDictEqual(data_1, data_2)
        checksums = {
            'djerba_config.json': 'ec2370dc76e494894d24139e07a19d12',
            'elba_config_1.json': 'c37c953b63227730d4009c7a0ec56896',
            'elba_config_2.json': 'c37c953b63227730d4009c7a0ec56896'
            }
        self.verify_checksums(checksums, out_dir)

class TestStudy(TestBase):

    """Tests for cBioPortal study generation"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_study_test_')
        # clinical patients/samples files currently identical, but this will change
        # temporarily removed mutation config from study_config.json, so some case lists are omitted
        self.base_checksums = {
            'data_cancer_type.txt': '31d0678d437a5305dcf8e76a9ccc40ff',
            'data_clinical_patients.txt': 'd6fb18fa41b196964b45603fa06daf93',
            'data_clinical_samples.txt': 'd6fb18fa41b196964b45603fa06daf93',
            'meta_cancer_type.txt': '19d950648288bb7428e8aaf5ee2939a0',
            'meta_clinical_patients.txt': 'd5b8ba2aa2b50eb4f63f41ccda817618',
            'meta_clinical_samples.txt': '3e02417baf608dacb4e5e2df0733c9cf',
            'meta_study.txt': '10fe55a5d41501b9081e8ad69915fce5',
            #'case_lists/cases_3way_complete.txt': 'b5e5d0c300b3365eda75955c1be1f405',
            #'case_lists/cases_cnaseq.txt': 'a02611d78ab9ef7d7ac6768a2b9042b7',
            'case_lists/cases_custom.txt': 'e9bd0b716cdca7b34f20a70830598c2d',
            #'case_lists/cases_sequenced.txt': '634dfc2e289fe6877c35b8ab6d31c091'
        }

    def test_dry_run(self):
        """Test meta file generation in dry run of cBioPortal study"""
        out_dir = os.path.join(self.tmp.name, 'study_dry_run')
        os.mkdir(out_dir)
        config_path = os.path.join(self.dataDir, 'study_config.json')
        with open(config_path) as configFile:
            config = json.loads(configFile.read())
        test_study = study(config, log_level=logging.CRITICAL)
        test_study.write_all(out_dir, dry_run=True)
        self.verify_checksums(self.base_checksums, out_dir)

    def test_mutation_extended(self):
        """Test a cBioPortal study with mutation data"""
        out_dir = os.path.join(self.tmp.name, 'study_mutation_extended')
        os.mkdir(out_dir)
        config_path = os.path.join(self.dataDir, 'study_config_mx.json')
        with open(config_path) as configFile:
            config = json.loads(configFile.read())
        test_study = study(config, log_level=logging.ERROR)
        test_study.write_all(out_dir)
        checksums = self.base_checksums.copy()
        # clinical patient/sample data differs from default
        extra_checksums = {
            'data_clinical_patients.txt': 'd6fb18fa41b196964b45603fa06daf93',
            'data_clinical_samples.txt': 'd6fb18fa41b196964b45603fa06daf93',
            'data_mutation_extended.maf': 'c612ebe2d46a8844387e1411993ee893',
            'meta_mutation_extended.txt': 'cc5684c4b1558fb3fc93d30945e3cfeb',
            'case_lists/cases_sequenced.txt': '093c0dff5731561d1253092b112bf880'
        }
        checksums.update(extra_checksums)
        self.verify_checksums(checksums, out_dir)

class TestValidator(unittest.TestCase):
    # TestBase methods not needed

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))

    def test(self):
        """Test validation of Djerba config against the schema"""
        config_names = [
            'study_config.json',
            'study_config_mx.json',
            'report_config_custom.json',
            'report_config_custom_with_nan.json',
            'report_config_custom_broken.json'
        ]
        for config_name in config_names:
            config_path = os.path.join(self.dataDir, config_name)
            with open(config_path) as configFile:
                config = json.loads(configFile.read())
            test_validator = validator(log_level=logging.CRITICAL)
            sample = 'OCT-01-0472-CAP'
            self.assertTrue(
                test_validator.validate(config, None),
                "Study config is valid"
            )
            self.assertTrue(
                test_validator.validate(config, sample),
                "Study config is valid with sample name"
            )
            args = [config, 'nonexistent_sample']
            self.assertRaises(
                DjerbaConfigError,
                test_validator.validate,
                *args
            )
            del config[constants.GENETIC_ALTERATIONS_KEY]
            args = [config, None]
            self.assertRaises(
                DjerbaConfigError,
                test_validator.validate,
                *args
            )

if __name__ == '__main__':
    unittest.main()
