#! /usr/bin/env python3

import couchdb2, gzip, hashlib, logging, json, jsonschema, os, random, subprocess, tempfile, unittest
import pandas as pd

from unittest.mock import Mock, patch

from djerba.metrics import mutation_extended_gene_metrics, mutation_extended_sample_metrics
from djerba.report import report, DjerbaReportError
from djerba.sample import sample
from djerba.study import study
from djerba.utilities import constants
from djerba.config import builder, validator, DjerbaConfigError

class TestBase(unittest.TestCase):

    #SCHEMA_PATH = '/.mounts/labs/gsi/modulator/sw/data/elba-config-schema-1.0.2/elba_config_schema.json' # path to Elba JSON schema
    # FIXME temporary path for testing schema modifications
    SCHEMA_PATH = '/u/ibancarz/tmp/elba_config_schema.json'
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_test_')

    def tearDown(self):
        self.tmp.cleanup()

    def write_tsv_omitting_columns(self, input_path, output_path, column_names):
        """Write a copy of a TSV file with particular columns removed"""
        df = pd.read_csv(input_path, sep="\t", index_col=False).drop(columns=column_names)
        df.to_csv(output_path, sep="\t", index=False)

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

class TestBuilder(TestBase):
    """Tests for Elba config builder"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.input_schema_path = os.path.realpath(
            os.path.join(self.testDir, '..', 'lib', 'djerba', 'data', 'input_schema.json')
        )
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_builder_test_')
        self.sample_id = "OCT-01-0472-CAP"
        self.seg_dir = '/.mounts/labs/gsiprojects/gsi/djerba/segmented'
        self.bed = '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/S31285117_Regions.bed'
        self.tcga = '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/tmb/tcga_tmbs.txt'
        self.vcf = '/.mounts/labs/gsiprojects/gsi/cBioGSI/data/reference/'+\
                'ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz'
        self.seg = os.path.join(self.seg_dir, 'OCT-01-0472-CAP.tumour.bam.varscanSomatic_Total_CN.seg')

    def test(self):
        """Test the builder class"""
        test_builder = builder(self.sample_id, log_level=logging.WARN)
        maf_dir = '/.mounts/labs/gsiprojects/gsi/djerba/mutation_extended'
        builder_args = {
            test_builder.CUSTOM_DIR_INPUT: self.dataDir,
            test_builder.GENE_TSV_INPUT: 'custom_gene_annotation.tsv', # gene_tsv
            test_builder.SAMPLE_TSV_INPUT: 'custom_sample_annotation.tsv', # sample_tsv
            test_builder.MAF_INPUT: os.path.join(maf_dir, 'somatic01.maf.txt.gz'),
            test_builder.BED_INPUT: self.bed,
            test_builder.CANCER_TYPE_INPUT: 'blca', # cancer_type
            test_builder.ONCOKB_INPUT: None,
            test_builder.TCGA_INPUT: self.tcga,
            test_builder.VCF_INPUT: self.vcf,
            test_builder.SEG_INPUT: self.seg
        }
        config = test_builder.build(builder_args)
        with open('/u/ibancarz/tmp/djerba_config.json', 'w') as out_file:
            print(json.dumps(config, indent=4, sort_keys=True), file=out_file)
        with open(os.path.join(self.dataDir, 'builder_expected_djerba_config.json')) as expected_file:
            expected = json.loads(expected_file.read())
        # ordering of items in genetic_alterations is fixed in the builder code
        expected[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = self.dataDir
        expected[constants.GENETIC_ALTERATIONS_KEY][1]['input_directory'] = maf_dir
        expected[constants.GENETIC_ALTERATIONS_KEY][2]['input_directory'] = self.seg_dir
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
        jsonschema.validate(elba_config, elba_schema) # returns None if valid; exception otherwise
        elba_report.write(elba_config, os.path.join(out_dir, out_name))
        checksums = {out_name: '5f6764af829169400f4e65deabb21b9d'}
        self.verify_checksums(checksums, out_dir)

    def test_cgi(self):
        """Test building from CGI inputs"""
        input_dir = '/.mounts/labs/gsiprojects/gsi/djerba/cgi_builder'
        # construct custom annotation files
        # this is preferred to maintaining multiple slightly-different test input files
        gene_custom = 'custom_gene_annotation.tsv'
        sample_custom = 'custom_sample_annotation.tsv'
        out_dir = os.path.join(self.tmp.name, 'djerba_cgi_builder_test')
        os.mkdir(out_dir)
        # generate custom gene annotation on the fly
        maf_path = os.path.join(
            input_dir, 'OCTCAP', 'OCT_011351', 'OCT_011351_Ov_P_OCT-01-1351-CAP', '1',
            'variantEffectPredictor', 'OCT_011351_Ov_P_OCT-01-1351-CAP.maf.gz'
        )
        self.write_custom_gene_annotation(os.path.join(out_dir, gene_custom), maf_path)
        # write custom sample annotation, omitting columns derived from CGI inputs to avoid conflicts
        drop = ['CANCER_TYPE', 'CANCER_TYPE_DESCRIPTION', 'CANCER_TYPE_DETAILED', 'SEQUENZA_PLOIDY',
                'SEQUENZA_PURITY_FRACTION']
        self.write_tsv_omitting_columns(
            os.path.join(self.dataDir, sample_custom), os.path.join(out_dir, sample_custom), drop
        )
        test_builder = builder(self.sample_id, log_level=logging.ERROR)
        builder_args = {
            test_builder.STUDY_ID_INPUT: 'OCTCAP',
            test_builder.PATIENT_ID_INPUT: 'OCT_011351',
            test_builder.ANALYSIS_UNIT_INPUT: 'OCT_011351_Ov_P_OCT-01-1351-CAP',
            test_builder.ONCOTREE_CODE_INPUT: 'Bowel',
            test_builder.VERSION_NUM_INPUT: 1,
            test_builder.DATA_DIR_INPUT: input_dir,
            test_builder.ONCOTREE_PATH_INPUT: None,
            test_builder.CUSTOM_DIR_INPUT: out_dir, # was self.dataDir,
            test_builder.GENE_TSV_INPUT: gene_custom,
            test_builder.SAMPLE_TSV_INPUT: sample_custom,
            test_builder.BED_INPUT: self.bed,
	    test_builder.CANCER_TYPE_INPUT: 'blca', # cancer_type
            test_builder.ONCOKB_INPUT: None,
            test_builder.TCGA_INPUT: self.tcga,
            test_builder.VCF_INPUT: self.vcf,
            test_builder.SEG_INPUT: self.seg
        }
        config = test_builder.build_from_cgi_inputs(builder_args)
        with open(os.path.join(self.dataDir, 'builder_expected_cgi_djerba_config.json')) as expected_file:
            expected = json.loads(expected_file.read())
        # replace dummy path for custom annotation
        expected[constants.GENETIC_ALTERATIONS_KEY][0]['input_directory'] = out_dir
        self.assertEqual(config, expected, "Djerba config matches expected values")
        # test writing a report with the generated Djerba config
        out_name = 'elba_report_config.json'
        elba_report = report(config, self.sample_id, log_level=logging.ERROR)
        elba_config = elba_report.get_report_config(replace_null=True)
        with open(self.SCHEMA_PATH) as schema_file:
            elba_schema = json.loads(schema_file.read())
        jsonschema.validate(elba_config, elba_schema) # returns None if valid; raises exception otherwise
        elba_report.write(elba_config, os.path.join(out_dir, out_name))
        checksums = {out_name: 'c5bcd02ab27a9b86edf71eadc3f8c3e3'}
        self.verify_checksums(checksums, out_dir)

    def write_custom_gene_annotation(self, output_path, maf_path):
        """
        Generate custom gene annotation on the fly; useful for large gene sets
        maf_path is used to find the gene names
        """
        random.seed(42) # set the seed so random values are consistent between tests
        maf_file = gzip.open(maf_path)
        hs = 'Hugo_Symbol'
        gene_names = pd.read_csv(maf_file, sep="\t", usecols=[hs], comment='#')[hs].to_list()
        custom_cols = ['Gene', 'Copy_State', 'Drug_Annotation', 'Exp_Percentile', 'Exp_Z_Score',
                       'Gene_Annotation', 'Whizbam_URL', 'Fusion', 'Mutation_Class',
                       'Variant_Classification', 'Oncogenic_Binary']
        out_file = open(output_path, 'w')
        print("\t".join(custom_cols), file=out_file)
        for gene in gene_names:
            outputs = [
                gene,
                'Neutral',
                'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                random.randint(0,100),
                'NA',
                'Nullam nulla lacus, gravida id metus ut, fermentum.',
                'http://example.com/whizbam/%s' % gene,
                'NA',
                'Somatic Nonsense Mutation',
                'NA'
            ]
            print("\t".join([str(x) for x in outputs]), file=out_file)
        out_file.close()

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
        checksum = {report_name: '57f42d44545860b6e0e6c6349aadaa08'}
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
            'djerba_config.json': 'a63ac6df2f6af016b997a96da346a5ab',
            'elba_config_1.json': '5f6764af829169400f4e65deabb21b9d',
            'elba_config_2.json': '5f6764af829169400f4e65deabb21b9d'
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
