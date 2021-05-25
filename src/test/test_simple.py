#! /usr/bin/env python3

import configparser
import hashlib
import json
import jsonschema
import os
import subprocess
import tempfile
import unittest
from jsonschema.exceptions import ValidationError
from djerba.simple.discover.search import searcher, MissingProvenanceError
from djerba.simple.extract.extractor import extractor
from djerba.simple.extract.sequenza import sequenza_extractor
from djerba.simple.build.reader import json_reader, mastersheet_reader, multiple_reader
from djerba.simple.runner import runner

class TestBase(unittest.TestCase):

    def getMD5(self, inputPath):
        md5 = hashlib.md5()
        with open(inputPath, 'rb') as f:
            md5.update(f.read())
        return md5.hexdigest()

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_simple_')
        self.tmpDir = self.tmp.name
        self.schema_path = '/home/iain/oicr/git/elba-config-schema/elba_config_schema.json'
        self.provenance_path = '/home/iain/oicr/workspace/djerba/test_data/'+\
            'pass01_panx_provenance.modified.tsv.gz'
        self.bed_path = '/home/iain/oicr/workspace/djerba/test_data/djerba/tmb/S31285117_Regions.bed'
        self.project = 'PASS01'
        self.donor = 'PANX_1249'

        with open(self.schema_path) as f:
            self.schema = json.loads(f.read())

    def tearDown(self):
        self.tmp.cleanup()

class TestExtractor(TestBase):

    def test_writeIniParams(self):
        # TODO sanitize the ini and commit to repo
        iniPath = '/home/iain/oicr/workspace/djerba/test_data/report_configuration.ini'
        outDir = '/home/iain/tmp/djerba/test'
        with open(iniPath) as iniFile:
            # prepend header required by configparser; TODO import from constants
            configString = "[%s]\n%s" % ('REPORT_CONFIG', iniFile.read())
        config = configparser.ConfigParser()
        config.read_string(configString)
        extractor(config, self.bed_path, outDir).run()
        sampleParamsPath = os.path.join(outDir, 'sample_params.json')
        self.assertEqual(self.getMD5(sampleParamsPath), 'c539ae365d6fc754a3bb9b074d618607')

class TestReader(TestBase):

    def setUp(self):
        super().setUp()
        self.config = []
        config_filenames = ['json_reader_config_%d.json' % i for i in range(1,4)]
        for name in config_filenames:
            with open(os.path.join(self.dataDir, name)) as f:
                self.config.append(json.loads(f.read()))

    def test_mastersheet_reader(self):
        ms_config_path = os.path.join(self.dataDir, 'mastersheet_reader_config.json')
        with open(ms_config_path) as f:
            ms_config = json.loads(f.read())
        ms_config['mastersheet_path'] = os.path.join(self.dataDir, 'mastersheet-v1.psv')
        reader = mastersheet_reader(ms_config, self.schema)
        patient_id = reader.get_sample_info().get_attribute('PATIENT_ID')
        self.assertEqual(patient_id, '123-456-789')

    def test_json_reader(self):
        # read a config path with all fields specified
        reader1 = json_reader(self.config[0], self.schema)
        self.assertEqual(reader1.total_genes(), 2)
        for gene in reader1.get_genes_list():
            self.assertEqual(len(gene.get_attributes()), 17)
        self.assertEqual(len(reader1.get_sample_info().get_attributes()), 34)
        self.assertTrue(reader1.is_complete())
        self.assertIsNone(jsonschema.validate(reader1.get_output(), self.schema))
        # insert a value not permitted by the schema; output validation now fails
        reader1.sample_info.attributes['ORDERING_PHYSICIAN'] = 999
        with self.assertRaises(ValidationError):
            reader1.get_output()
        # read an incomplete config path
        reader2 = json_reader(self.config[1], self.schema)
        self.assertEqual(reader2.total_genes(), 2)
        for gene in reader2.get_genes_list():
            self.assertEqual(len(gene.get_attributes()), 9)
        self.assertEqual(len(reader2.get_sample_info().get_attributes()), 14)
        self.assertFalse(reader2.is_complete())
        with self.assertRaises(RuntimeError):
            reader2.get_output()

    def test_multiple_reader(self):
        # multiple reader with consistent values
        reader1 = multiple_reader(self.config[0:2], self.schema)
        self.assertEqual(reader1.total_genes(), 2)
        for gene in reader1.get_genes_list():
            self.assertEqual(len(gene.get_attributes()), 17)
        self.assertEqual(len(reader1.get_sample_info().get_attributes()), 34)
        self.assertTrue(reader1.is_complete())
        self.assertIsNone(jsonschema.validate(reader1.get_output(), self.schema))
        # inconsistent values
        with self.assertRaises(ValueError):
            reader2 = multiple_reader([self.config[0], self.config[2]], self.schema)

class TestRunner(TestBase):

    def setUp(self):
        super().setUp()
        self.expectedMD5 = '2a1d86db2248f90aef4b7a7dc6698bfc'
        self.iniPath = '/home/iain/oicr/workspace/djerba/test_data/report_configuration.ini'
        self.workDir = os.path.join(self.tmpDir, 'work')
        os.mkdir(self.workDir)
        
    def test_runner(self):
        #outPath = os.path.join(self.tmpDir, 'report.json')
        outDir = '/home/iain/tmp/djerba/test'
        outPath = os.path.join(outDir, 'report.json')
        runner(self.provenance_path,
               self.project,
               self.donor,
               self.bed_path,
               self.iniPath,
               self.workDir,
               outPath,
               self.schema_path).run()
        self.assertEqual(self.getMD5(outPath), self.expectedMD5)

    def test_script(self):
        outDir = '/home/iain/tmp/djerba/script' # TODO replace with tempdir
        outPath = os.path.join(outDir, 'report.json')
        cmd = [
            "djerba_simple.py",
            "--provenance", self.provenance_path,
            "--project", self.project,
            "--donor", self.donor,
            "--bed", self.bed_path,
            "--ini", self.iniPath,
            "--out", outPath,
            "--schema", self.schema_path,
            "--ini", self.iniPath,
            "--work-dir", self.workDir
        ]
        subprocess.run(cmd)
        self.assertEqual(self.getMD5(outPath), self.expectedMD5)

class TestSearcher(TestBase):

    def test_searcher(self):
        test_searcher = searcher(self.provenance_path, self.project, self.donor)
        maf_path = test_searcher.parse_maf_path()
        expected = '/home/iain/oicr/workspace/djerba/test_data/djerba/tmb/PANX_1249_Lv_M_WG_100-PM-013_LCM5.filter.deduped.realigned.recalibrated.mutect2.tumor_only.filtered.unmatched.DUMMY.maf.gz'
        self.assertEqual(maf_path, expected)
        with self.assertRaises(MissingProvenanceError):
            test_searcher_2 = searcher(self.provenance_path, self.project, 'nonexistent_donor')

class TestSequenzaExtractor(TestBase):

    def test(self):
        zip_path = '/home/iain/oicr/workspace/djerba/test_data/sequenza/PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip'
        seqex = sequenza_extractor(zip_path)
        [purity, ploidy] = seqex.get_purity_ploidy()
        self.assertEqual(purity, 0.6)
        self.assertEqual(ploidy, 3.1)
        expected_segments = {
            50: 8669,
            100: 4356,
            200: 1955,
            300: 1170,
            400: 839,
            500: 622,
            600: 471,
            700: 407,
            800: 337,
            900: 284,
            1000: 245,
            1250: 165,
            1500: 123,
            2000: 84
        }
        self.assertEqual(seqex.get_segments(), expected_segments)
        self.assertEqual(seqex.get_default_gamma(), 400)


if __name__ == '__main__':
    unittest.main()
