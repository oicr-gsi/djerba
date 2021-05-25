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
        self.default_gamma = self.find_default_gamma()

    def _count_segments(self, seg_path):
        """Count the number of segments; equal to length of file, excluding the header"""
        with open(seg_path) as seg:
            length = len(seg.readlines())
        return length - 1

    def _find_default_gamma(self):
        """
        Gamma heuristic:
        - Draw a straight line between least and greatest gamma (usually 50 and 2000, respectively)
        - We want to find the transition from steeper-than-linear to shallower-than-linear
        - Compare actual gradient between N-1th and Nth gamma with expected linear gradient
        - (This takes account of non-equal gamma intervals)
        - When actual gradient is less in magnitude than expected gradient, stop and use Nth gamma
        """
        gammas = sorted(list(self.segments.keys()))
        gamma_min = gammas[0]
        gamma_max = gammas[-1]
        delta_y = self.segments[gamma_max] - self.segments[gamma_min]
        delta_x = gamma_max - gamma_min
        linear_gradient = float(delta_y)/delta_x
        chosen_gamma = None
        for i in range(1, len(gammas)):
            delta_y = self.segments[gammas[i]] - self.segments[gammas[i-1]]
            delta_x = gammas[i] - gammas[i-1]
            gradient = float(delta_y)/delta_x
            if abs(gradient) <= abs(linear_gradient):
                chosen_gamma = gammas[i]
                break
        return chosen_gamma

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

    def get_default_gamma(self):
        return self.default_gamma

    def get_purity_ploidy(self, gamma=None):
        """Get purity and ploidy for supplied gamma (if any), default gamma otherwise"""
        if gamma==None:
            gamma = self.default_gamma
        return self.metrics[gamma]

    def get_segments(self):
        return self.segments

class MissingDataError(Exception):
    pass
