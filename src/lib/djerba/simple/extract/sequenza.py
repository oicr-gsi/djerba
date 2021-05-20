"""Extract metrics from Sequenza results; gamma parameter can be chosen automatically or supplied by the user"""

import csv
import os
import re
import tempfile
import zipfile
from glob import glob

class sequenza_extractor:

    def __init__(self, zip_path):
        """Decompress the zip archive to a temporary directory; read relevant values"""
        tempdir = tempfile.TemporaryDirectory(prefix='djerba_sequenza_')
        tmp = tempdir.name
        # zip archives are large (~500 MB) -- only extract the files we need
        zf = zipfile.ZipFile(zip_path)
        for name in zf.namelist():
            if re.search('_(segments|alternative_solutions)\.txt$', name):
                zf.extract(name, tmp)
        gamma_dir = os.path.join(tmp, 'gammas')
        gamma_names = os.listdir(gamma_dir)
        self.segments = {}
        self.metrics = {}
        for gamma_name in gamma_names:
            seg = glob(os.path.join(gamma_dir, gamma_name, '*_segments.txt'))
            sol = glob(os.path.join(gamma_dir, gamma_name, '*_alternative_solutions.txt'))
            if len(seg)!=1 or len(sol)!=1:
                msg = "Incorrect number of segment/solution files in " +\
                    "%s for gamma %s; should have one of each" % (zip_path, gamma_name)
                raise MissingDataError(msg)
            gamma = int(gamma_name)
            self.segments[gamma] = self._count_segments(seg[0])
            self.metrics[gamma] = self._find_purity_ploidy(sol[0])
        tempdir.cleanup()

    def _count_segments(self, seg_path):
        """Count the number of segments; equal to length of file, excluding the header"""
        with open(seg_path) as seg:
            length = len(seg.readlines())
        return length - 1

    def _find_default_gamma(self):
        """TODO implement heuristic for finding default gamma from segement counts"""
        return 400

    def _find_purity_ploidy(self, sol_path):
        """Find most probable purity/ploidy from an alternative_solutions.txt file"""
        with open(sol_path, 'rt') as sol_file:
            reader = csv.reader(sol_file, delimiter="\t")
            first = True
            [purity, ploidy] = [None, None]
            for row in reader:
                if first: # skip the header row
                    first = False
                else:
                    purity = float(row[0])
                    ploidy = float(row[1])
                    break
        return [purity, ploidy]

    def get_purity_ploidy(self, gamma=None):
        """Get purity and ploidy for supplied gamma (if any), default gamma otherwise"""
        if gamma==None:
            gamma = self._find_default_gamma()
        return self.metrics[gamma]

    def get_segments(self):
        return self.segments

class MissingDataError(Exception):
    pass
