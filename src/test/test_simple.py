#! /usr/bin/env python3

import hashlib
import json
import jsonschema
import os
import tempfile
import unittest
from jsonschema.exceptions import ValidationError
from djerba.simple.preprocess.processor import processor
from djerba.simple.build.reader import json_reader, mastersheet_reader, multiple_reader

class TestProcessor(unittest.TestCase):

    def getMD5(self, inputPath):
        md5 = hashlib.md5()
        with open(inputPath, 'rb') as f:
            md5.update(f.read())
        return md5.hexdigest()

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_simple_test_processor_')
        self.tmpDir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_writeIniParams(self):
        # TODO sanitize the ini and commit to repo
        iniPath = '/home/iain/oicr/workspace/djerba/test_data/PANX_1249_Lv_M_100-PM-013_LCM5/1/report/report_configuration.ini'
        outDir = '/home/iain/tmp/djerba/test'
        processor(iniPath, outDir).run()
        sampleParamsPath = os.path.join(outDir, 'sample_params.json')
        self.assertEqual(self.getMD5(sampleParamsPath), '26757d8f945df33087bbe47c328dcf22')
    
class TestReader(unittest.TestCase):

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        schema_path = '/home/iain/oicr/git/elba-config-schema/elba_config_schema.json'
        with open(schema_path) as f:
            self.schema = json.loads(f.read())
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

if __name__ == '__main__':
    unittest.main()
