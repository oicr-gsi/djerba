#! /usr/bin/env python3

import os
import unittest

from fga import find_fga

class TestSampleMetrics(unittest.TestCase):

    def setUp(self):
        self.data_dir = '/.mounts/labs/gsiprojects/gsi/janus/prototypes/'
        self.delta = 10**(-10)

    def test_fga(self):
        """Test the Fraction Genome Altered metric"""
        seg_path = os.path.join(self.data_dir, 'fga', 'data_segments.txt')
        sampleName = "COM-00278-CAP"
        expected_fga = 0.452404008036
        fga = find_fga(seg_path, sampleName)
        self.assertTrue(abs(fga - expected_fga) < self.delta)

if __name__ == '__main__':
    unittest.main()
