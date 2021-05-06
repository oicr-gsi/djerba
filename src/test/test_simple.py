#! /usr/bin/env python3

import json
import os
import unittest

from djerba.simple.reader import json_reader

class TestReader(unittest.TestCase):

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
    
    def test_json_reader(self):
        # TODO make 2 readers and use to update, starting with an empty structure
        # read a config path with all fields specified
        config_path_1 = os.path.join(self.dataDir, 'simple_config_1.json')
        with open(config_path_1) as f:
            config = json.loads(f.read())
        schema_path = '/home/iain/oicr/git/elba-config-schema/elba_config_schema.json'
        reader = json_reader(config, schema_path)
        gene_metrics = reader.update_genes([])
        self.assertEqual(len(gene_metrics), 2)
        sample_info = reader.update_sample({})
        self.assertEqual(len(sample_info), 34)
        # update with consistent values; works fine
        config_path_2 = os.path.join(self.dataDir, 'simple_config_2.json')
        with open(config_path_2) as f:
            config = json.loads(f.read())
        reader = json_reader(config, schema_path)
        gene_metrics = reader.update_genes(gene_metrics)
        self.assertEqual(len(gene_metrics), 2)
        sample_info = reader.update_sample(sample_info)
        self.assertEqual(len(sample_info), 34)
        # update again with inconsistent values; fails
        config_path_3 = os.path.join(self.dataDir, 'simple_config_3.json')
        with open(config_path_3) as f:
            config = json.loads(f.read())
        reader = json_reader(config, schema_path)
        with self.assertRaises(ValueError):
            gene_metrics = reader.update_genes(gene_metrics)
        with self.assertRaises(ValueError):
            sample_info = reader.update_sample(sample_info)

        
if __name__ == '__main__':
    unittest.main()
