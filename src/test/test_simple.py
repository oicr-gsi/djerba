#! /usr/bin/env python3

import json
import jsonschema
import os
import unittest

from djerba.simple.reader import json_reader

class TestReader(unittest.TestCase):

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
    
    def test_json_reader(self):
        schema_path = '/home/iain/oicr/git/elba-config-schema/elba_config_schema.json'
        # read a config path with all fields specified
        config_path_1 = os.path.join(self.dataDir, 'simple_config_1.json')
        with open(config_path_1) as f:
            config1 = json.loads(f.read())
        reader = json_reader(schema_path)
        reader.update(config1)
        self.assertEqual(len(reader.get_genes()), 2)
        for gene in reader.get_genes().values():
            self.assertEqual(len(gene.get_attributes()), 17)
        self.assertEqual(len(reader.get_sample_info().get_attributes()), 34)
        self.assertTrue(reader.is_complete())
        # update with consistent values
        config_path_2 = os.path.join(self.dataDir, 'simple_config_2.json')
        with open(config_path_2) as f:
            config2 = json.loads(f.read())
        reader.update(config2)
        self.assertEqual(len(reader.get_genes()), 2)
        for gene in reader.get_genes().values():
            self.assertEqual(len(gene.get_attributes()), 17)
        self.assertEqual(len(reader.get_sample_info().get_attributes()), 34)
        self.assertTrue(reader.is_complete())
        # update with inconsistent values (fails)
        config_path_3 = os.path.join(self.dataDir, 'simple_config_3.json')
        with open(config_path_3) as f:
            config3 = json.loads(f.read())
        with self.assertRaises(ValueError):
            reader.update(config3)
        # make a new reader with partial values
        reader2 = json_reader(schema_path)
        reader2.update(config2)
        self.assertEqual(len(reader2.get_genes()), 2)
        for gene in reader2.get_genes().values():
            self.assertEqual(len(gene.get_attributes()), 9)
        self.assertEqual(len(reader2.get_sample_info().get_attributes()), 14)
        self.assertFalse(reader2.is_complete())
        # update with remaining values
        reader2.update(config3)
        self.assertEqual(len(reader2.get_genes()), 2)
        for gene in reader2.get_genes().values():
            self.assertEqual(len(gene.get_attributes()), 17)
        self.assertEqual(len(reader2.get_sample_info().get_attributes()), 34)
        self.assertTrue(reader2.is_complete())
        with open(schema_path) as f:
            schema = json.loads(f.read())
        # generate output and validate against schema
        jsonschema.validate(reader2.get_output(), schema)


if __name__ == '__main__':
    unittest.main()
