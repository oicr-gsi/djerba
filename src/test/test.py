#! /usr/bin/env python3

import couchdb2, hashlib, logging, json, jsonschema, os, random, subprocess, tempfile, unittest

from unittest.mock import Mock, patch

from djerba.metrics import mutation_extended_gene_metrics, mutation_extended_sample_metrics
from djerba.report import report, DjerbaReportError
from djerba.sample import sample
from djerba.study import study
from djerba.utilities import constants
from djerba.config import builder, validator, DjerbaConfigError

class TestBase(unittest.TestCase):

    SCHEMA_PATH = '/.mounts/labs/gsi/modulator/sw/data/elba-config-schema-1.0.2/elba_config_schema.json' # path to Elba JSON schema
    
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
        """Test the builder class"""
        test_builder = builder(self.sample_id, log_level=logging.WARN)
        maf_dir = '/.mounts/labs/gsiprojects/gsi/djerba/mutation_extended'
        seg_dir = '/.mounts/labs/gsiprojects/gsi/djerba/segmented'
        bed = '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/S31285117_Regions.bed'
        tcga = '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/tcga_tmbs.txt'
        vcf = '/.mounts/labs/gsiprojects/gsi/cBioGSI/data/reference/'+\
              'ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz'
        seg = os.path.join(seg_dir, 'OCT-01-0472-CAP.tumour.bam.varscanSomatic_Total_CN.seg')
        builder_args = {
            test_builder.CUSTOM_DIR_INPUT: self.dataDir,
            test_builder.GENE_TSV_INPUT: 'custom_gene_annotation.tsv', # gene_tsv
            test_builder.SAMPLE_TSV_INPUT: 'custom_sample_annotation.tsv', # sample_tsv
            test_builder.MAF_INPUT: os.path.join(maf_dir, 'somatic01.maf.txt.gz'),
            test_builder.BED_INPUT: bed,
            test_builder.CANCER_TYPE_INPUT: 'blca', # cancer_type
            test_builder.ONCOKB_INPUT: None,
            test_builder.TCGA_INPUT: tcga,
            test_builder.VCF_INPUT: vcf,
            test_builder.SEG_INPUT: seg
        }
        config = test_builder.build(builder_args)
        with open(os.path.join(self.dataDir, 'builder_expected_djerba_config.json')) as expected_file:
            expected = json.loads(expected_file.read())
        # ordering of items in genetic_alterations is fixed in the builder code
        expected[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = self.dataDir
        expected[constants.GENETIC_ALTERATIONS_KEY][1]['input_directory'] = maf_dir
        expected[constants.GENETIC_ALTERATIONS_KEY][2]['input_directory'] = seg_dir
        #self.maxDiff = None # uncomment to show unlimited JSON diff
        self.assertEqual(config, expected, "Djerba config matches expected values")
        # test writing a report with the generated Djerba config
        out_name = 'elba_report_config.json'
        out_dir = os.path.join(self.tmp.name, 'djerba_builder_test')
        os.mkdir(out_dir)
        elba_report = report(config, self.sample_id, log_level=logging.ERROR)
        elba_config = elba_report.get_report_config(replace_null=True)
        with open(self.SCHEMA_PATH) as schema_file:
            elba_schema = json.loads(schema_file.read())
        jsonschema.validate(elba_config, elba_schema) # returns None if valid; raises exception otherwise
        elba_report.write(elba_config, os.path.join(out_dir, out_name))
        checksums = {out_name: '5c6dea4fc34c28de6c636a060971d39a'}
        self.verify_checksums(checksums, out_dir)

    def test_cgi(self):
        """Test building from CGI inputs"""
        test_builder = builder(self.sample_id, log_level=logging.WARN)
        """
        # TODO update the builder args
        builder_args = {
            test_builder.CUSTOM_DIR_INPUT: self.dataDir,
            test_builder.GENE_TSV_INPUT: 'custom_gene_annotation.tsv', # gene_tsv
            test_builder.SAMPLE_TSV_INPUT: 'custom_sample_annotation.tsv', # sample_tsv
            test_builder.MAF_INPUT: os.path.join(maf_dir, 'somatic01.maf.txt.gz'),
            test_builder.BED_INPUT: bed,
            test_builder.CANCER_TYPE_INPUT: 'blca', # cancer_type
            test_builder.ONCOKB_INPUT: None,
            test_builder.TCGA_INPUT: tcga,
            test_builder.VCF_INPUT: vcf,
            test_builder.SEG_INPUT: seg
        }
        """

class TestMetrics(TestBase):
    """Tests for genetic alteration metrics"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = '/.mounts/labs/gsiprojects/gsi/djerba/mutation_extended'
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_mx_metrics_test_')

    def test_mx_gene_metrics(self):
        """Test gene-level mutation extended metrics"""
        subdir = 'gene_metrics'
        maf_path = os.path.join(self.data_dir, subdir, 'data_mutations_extended.txt')
        mx_gene_metrics = mutation_extended_gene_metrics(maf_path)
        metrics = mx_gene_metrics.get_metrics()
        out_dir = os.path.join(self.tmp.name, 'mx_gene_metrics')
        os.mkdir(out_dir)
        out_name = 'mx_gene_metrics.json'
        with open(os.path.join(out_dir, out_name), 'w') as out_file:
            print(json.dumps(metrics, indent=4, sort_keys=True), file=out_file)
        checksums = {out_name: '559f46232347a17425577ed347390bf8'}
        self.verify_checksums(checksums, out_dir)

    def test_mx_tmb(self):
        """Test the Tumor Mutation Burden metric"""
        subdir = 'sample_metrics'
        maf_path = os.path.join(self.data_dir, subdir, 'somatic.maf.txt.gz')
        bed_path = os.path.join(self.data_dir, subdir, 'S31285117_Regions.bed')
        tcga_path = os.path.join(self.data_dir, subdir, 'tcga_tmbs.txt')
        cancer_type = "blca"
        with open(os.path.join(self.data_dir, subdir, 'tmb_expected.json')) as exp_file:
            expected = json.loads(exp_file.read())
        mx_sample_metrics = mutation_extended_sample_metrics(maf_path, bed_path, tcga_path, cancer_type)
        output = [
            mx_sample_metrics.get_tmb(),
            mx_sample_metrics.get_tcga_pct(),
            mx_sample_metrics.get_cohort_pct(),
            mx_sample_metrics.get_tcga_tmb_as_dict(),
            mx_sample_metrics.get_cohort_tmb_as_dict(),
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

    # TODO test reporting with more non-standard or incorrect inputs; eg. NA values, missing samples

    def test(self):
        """
        Test report with genetic alterations
        """
        report_name = 'report.json'
        out_dir = os.path.join(self.tmp.name, 'test_report_custom')
        os.mkdir(out_dir)
        with open(os.path.join(self.dataDir, 'report_config.json')) as configFile:
            config = json.loads(configFile.read())
        # get custom config input from the local test directory
        config[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = self.dataDir
        report_path = os.path.join(out_dir, report_name)
        test_report = report(config, self.sample_id, self.SCHEMA_PATH, log_level=logging.ERROR)
        test_report.write(test_report.get_report_config(), report_path)
        self.assertTrue(os.path.exists(report_path), "JSON report exists")
        checksum = {report_name: '8405eeb825de623446dc24c613408e18'}
        self.verify_checksums(checksum, out_dir)
        args = [config, 'nonexistent sample', self.SCHEMA_PATH, logging.CRITICAL]
        self.assertRaises(DjerbaReportError, report, *args)

    def test_upload(self):
        """Test uploading the report JSON to mock Elba instances"""
        # This tests the child 'report' class; TODO add a separate test for the parent 'uploader' class
        with open(os.path.join(self.dataDir, 'report_config.json')) as configFile:
            djerba_config = json.loads(configFile.read()) # same config as test_mx
        djerba_config[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = self.dataDir
        test_report = report(djerba_config, self.sample_id, self.SCHEMA_PATH, log_level=logging.ERROR)
        db_name = 'cgi_report'
        elba_config = test_report.get_report_config(replace_null=True)
        os.environ[constants.ELBA_DB_USER] = 'test_elba_user'
        os.environ[constants.ELBA_DB_PASSWORD] = 'test_elba_password'
        with patch('couchdb2.Server') as server_class, self.assertLogs(test_report.logger) as test_log:
            mock_server_instance = server_class.return_value
            mock_db_instance = Mock()
            mock_server_instance.get.return_value = mock_db_instance
            test_report.upload(elba_config)
            mock_server_instance.get.assert_called_with(db_name)
            mock_db_instance.put.assert_called_with(elba_config)
            self.assertEqual(test_log.output.pop(), 'INFO:djerba.report.report:Uploaded config to Elba server')

class TestScripts(TestBase):
    """Tests of command-line scripts"""

    def setUp(self):
        super().setUp()
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.binDir =  os.path.realpath(os.path.join(self.testDir, os.pardir, 'bin'))
        self.scriptNames = ['djerba.py', 'djerba_from_command.py', 'upload.py']

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
            '--seg',
            '/.mounts/labs/gsiprojects/gsi/djerba/segmented/OCT-01-0472-CAP.tumour.bam.varscanSomatic_Total_CN.seg',
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
            'djerba_config.json': '03cde7e832df481c22f33c7d2381e27d',
            'elba_config_1.json': '5c6dea4fc34c28de6c636a060971d39a',
            'elba_config_2.json': '5c6dea4fc34c28de6c636a060971d39a'
            }
        self.verify_checksums(checksums, out_dir)

class TestStudy(TestBase):

    """Tests for cBioPortal study generation"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_study_test_')
        # clinical patients/samples files currently identical, but this will change
        self.base_checksums = {
            'data_cancer_type.txt': '31d0678d437a5305dcf8e76a9ccc40ff',
            'data_clinical_patients.txt': 'd6fb18fa41b196964b45603fa06daf93',
            'data_clinical_samples.txt': 'd6fb18fa41b196964b45603fa06daf93',
            'meta_cancer_type.txt': '19d950648288bb7428e8aaf5ee2939a0',
            'meta_clinical_patients.txt': 'd5b8ba2aa2b50eb4f63f41ccda817618',
            'meta_clinical_samples.txt': '3e02417baf608dacb4e5e2df0733c9cf',
            'meta_study.txt': '10fe55a5d41501b9081e8ad69915fce5',
            'case_lists/cases_custom.txt': 'e9bd0b716cdca7b34f20a70830598c2d',
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

    def test_live(self):
        """Test a cBioPortal study with mutation data"""
        out_dir = os.path.join(self.tmp.name, 'study_mutation_extended')
        os.mkdir(out_dir)
        config_path = os.path.join(self.dataDir, 'study_config.json')
        with open(config_path) as configFile:
            config = json.loads(configFile.read())
        test_study = study(config, log_level=logging.ERROR)
        test_study.write_all(out_dir)
        checksums = self.base_checksums.copy()
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
            'report_config.json',
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
