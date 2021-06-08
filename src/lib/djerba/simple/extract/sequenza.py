"""Extract metrics from Sequenza results; gamma parameter can be chosen automatically or supplied by the user"""

import csv
import os
import re
import shutil
import sys
import tempfile
import zipfile
from glob import glob

class sequenza_extractor:

    def __init__(self, zip_path, out_file=None):
        """
        Decompress the zip archive to a temporary directory
        Read values for default gamma, and purity/ploidy
        """
        self.zip_path = zip_path
        self.segment_counts = {}
        self.metrics = {}
        self.seg_archive = {} # archive paths to .seg files
        self.gammas = []
        tempdir = tempfile.TemporaryDirectory(prefix='djerba_sequenza_')
        tmp = tempdir.name
        # zip archives are large (~500 MB) -- only extract the files we need
        # Sequenza archives *should* have correct file contents, but we do some basic sanity checking
        gamma_set = set()
        zf = zipfile.ZipFile(self.zip_path)
        multiple_files = False
        for name in zf.namelist():
            if re.search('/sol[0-9]_', name):
                continue # exclude Sequenza's lower-probability alternative results
            terms = re.split(os.sep, name)
            try:
                gamma = int(terms[1])
            except Exception as exc:
                msg = "Unable to parse gamma parameter from {0} ".format(name) +\
                    "in archive {0}".format(self.zip_path)
                raise SequenzaExtractionError(msg) from exc
            gamma_set.add(gamma)
            if re.search('_segments\.txt$', name):
                if gamma in self.segment_counts: multiple_files = True
                self.segment_counts[gamma] = self._count_segments(zf.extract(name, tmp))
            elif re.search('_alternative_solutions\.txt$', name):
                if gamma in self.metrics: multiple_files = True
                self.metrics[gamma] = self._find_purity_ploidy(zf.extract(name, tmp))
            elif re.search('_Total_CN.seg', name):
                if gamma in self.seg_archive: multiple_files = True
                self.seg_archive[gamma] = name
        if multiple_files:
            msg = "Multiple files of same type in Sequenza archive {0}".format(self.zip_path)
            raise SequenzaExtractionError(msg)
        tempdir.cleanup()
        self.gammas = sorted(list(gamma_set))
        total = len(self.gammas)
        if len(self.segment_counts)!=total or len(self.metrics)!=total or len(self.seg_archive)!=total:
            raise SequenzaExtractionError("Inconsistent number of files in {0}".format(self.zip_path))
        self.default_gamma = self._find_default_gamma(out_file)

    def _count_segments(self, seg_path):
        """Count the number of segments; equal to length of file, excluding the header"""
        with open(seg_path) as seg:
            length = len(seg.readlines())
        return length - 1

    def _find_default_gamma(self, out_file=None):
        """
        Gamma heuristic:
        - Draw a straight line between least and greatest gamma (usually 50 and 2000, respectively),
          to get the "expected gradient"
        - We want to find the transition from steeper-than-linear to shallower-than-linear
        - Compare actual gradient between N-1th and Nth gamma with expected linear gradient
        - (This takes account of non-equal gamma intervals)
        - When actual gradient is less in magnitude than expected gradient, stop and use Nth gamma
        - Optionally, write parameters as TSV
        """
        gamma_min = self.gammas[0]
        gamma_max = self.gammas[-1]
        delta_y = self.segment_counts[gamma_max] - self.segment_counts[gamma_min]
        delta_x = gamma_max - gamma_min
        linear_gradient = float(delta_y)/delta_x
        chosen_gamma = None
        if out_file:
            print("\t".join(['gamma', 'segments', 'gradient', 'expected']), file=out_file)
            fields = [self.gammas[0], self.segment_counts[self.gammas[0]], 'NA', 'NA']
            print("\t".join([str(x) for x in fields]), file=out_file)
        for i in range(1, len(self.gammas)):
            delta_y = self.segment_counts[self.gammas[i]] - self.segment_counts[self.gammas[i-1]]
            delta_x = self.gammas[i] - self.gammas[i-1]
            gradient = float(delta_y)/delta_x
            fields = [
                self.gammas[i],
                self.segment_counts[self.gammas[i]],
                gradient,
                linear_gradient
            ]
            if out_file:
                print("\t".join([str(x) for x in fields]), file=out_file)
            if abs(gradient) <= abs(linear_gradient) and chosen_gamma==None:
                chosen_gamma = self.gammas[i]
                if not out_file:
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

    def _gamma_not_found_message(self, gamma):
        valid = sorted(list(self.segment_counts.keys()))
        msg = "gamma={0} not found in '{1}'; ".format(gamma, self.zip_path) +\
            "available gammas are: {0}".format(str(self.gammas))
        return msg
    
    def extract_seg_file(self, dest_dir, gamma=None):
        """
        Extract the Total_CN.seg file; for the supplied gamma (if any), default gamma otherwise.
        dest_dir is a directory path for the extracted file.
        The .seg file is further processed downstream, before input to singleSample.R
        """
        if gamma == None:
            gamma = self.default_gamma
        if gamma in self.gammas:
            zf = zipfile.ZipFile(self.zip_path)
            extracted = zf.extract(self.seg_archive[gamma], dest_dir)
        else:
            raise SequenzaExtractionError(self._gamma_not_found_message(gamma))
        return extracted

    def get_default_gamma(self):
        return self.default_gamma

    def get_purity_ploidy(self, gamma=None):
        """Get purity and ploidy for supplied gamma (if any), default gamma otherwise"""
        if gamma == None:
            gamma = self.default_gamma
        if gamma in self.metrics:
            return self.metrics[gamma]
        else:
            raise SequenzaExtractionError(self._gamma_not_found_message(gamma))

    def get_segment_counts(self):
        return self.segment_counts


class SequenzaExtractionError(Exception):
    pass
