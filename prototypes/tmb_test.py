#! /usr/bin/env python3

import os
import unittest

from prototypes.tmb import find_tmb

class TestSampleMetrics(unittest.TestCase):

    def setUp(self):
        self.data_dir = '/.mounts/labs/gsiprojects/gsi/janus/prototypes/'
        self.delta = 10**(-10)

# need to discuss how to do this when there are multiple function outputs
    def test_tmb(self):
        """Test the Fraction Genome Altered metric"""
        maf_path = os.path.join(self.data_dir, 'tmb', 'somatic.maf.txt.gz')
        bed_path = os.path.join(self.data_dir, 'tmb', 'S31285117_Regions.bed')
        tcga_path = os.path.join(self.data_dir, 'tmb', 'tcga_tmbs.txt')
        expected_path = os.path.join(self.data_dir, 'tmb', 'tcga_tmbs.txt')
        expected =
        output = find_tmb(maf_path, bed_path, tcga_path, cancer_type)
        for i in range(len(output)):
            self.assertEqual(output[i], expected[i])

if __name__ == '__main__':
    unittest.main()