#! /usr/bin/env python3

import json
import os
import unittest

from prototypes.tmb import find_tmb

class TestSampleMetrics(unittest.TestCase):

    def setUp(self):
        self.data_dir = '/.mounts/labs/gsiprojects/gsi/djerba/prototypes/'
        self.delta = 10**(-10)

# need to discuss how to do this when there are multiple function outputs
    def test_tmb(self):
        """Test the Tumor Mutation Burden metric"""
        maf_path = os.path.join(self.data_dir, 'tmb', 'somatic.maf.txt.gz')
        bed_path = os.path.join(self.data_dir, 'tmb', 'S31285117_Regions.bed')
        tcga_path = os.path.join(self.data_dir, 'tmb', 'tcga_tmbs.txt')
        cancer_type = "blca"
        with open(os.path.join(self.data_dir, 'tmb_expected.json')) as exp_file:
            expected = json.loads(exp_file.read())
        output = find_tmb(maf_path, bed_path, tcga_path, cancer_type)
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

if __name__ == '__main__':
    unittest.main()
