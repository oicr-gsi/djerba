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
        cancer_type = "blca"
        expected_tmb = 3.0236235709599097
        expected_tmb_pct = 0.5156686317095873
        expected_tmb_cohort_pct = 0.17603911980440098
        expected = [expected_tmb, expected_tmb_pct, expected_tmb_cohort_pct]
        output = find_tmb(maf_path, bed_path, tcga_path, cancer_type)
        for i in range(len(output)):
            self.assertEqual(output[i], expected[i])

if __name__ == '__main__':
    unittest.main()