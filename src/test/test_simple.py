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
        config_path = os.path.join(self.dataDir, 'simple_config.json')
        with open(config_path) as f:
            config = json.loads(f.read())
        schema_path = '/home/iain/oicr/git/elba-config-schema/elba_config_schema.json'
        reader = json_reader(config, schema_path)
        gene_metrics = reader.update_genes({})
        sample_info = reader.update_sample({})
        self.assertTrue(1)

        
if __name__ == '__main__':
    unittest.main()
