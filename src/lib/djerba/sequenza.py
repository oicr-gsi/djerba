"""Extract metrics from Sequenza results; gamma parameter can be chosen automatically or supplied by the user"""

import csv
import json
import logging
import math
import os
import re
import sys
import tempfile
import zipfile

import djerba.util.constants as constants
from djerba.util.logger import logger

class sequenza_reader(logger):

    def __init__(self, zip_path, log_level=logging.WARNING, log_path=None):
        """
        Decompress the zip archive to a temporary directory
        Read values for gamma and purity/ploidy; find default gamma
        """
        self.zip_path = zip_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.segment_counts = {}
        self.purity = {}
        self.ploidy = {}
        self.seg_archive = {} # archive paths to .seg files
        self.Aratio_archive = {} #archive paths to aratio_segments.txt
        tempdir = tempfile.TemporaryDirectory(prefix='djerba_sequenza_')
        tmp = tempdir.name
        # zip archives are large (~500 MB) -- only extract the files we need
        # Sequenza archives *should* have correct file contents, but we do some basic sanity checking
        # 'gamma id' is the value of gamma, plus the solution designator ('primary', 'sol2_0.49', etc.)
        zf = zipfile.ZipFile(self.zip_path)
        gamma_id_set = set()
        # first pass -- populate the canonical set of gamma IDs
        for name in zf.namelist():
            gamma_id = self._parse_gamma_id(name)
            gamma_id_set.add(gamma_id)
        self.gamma_ids = sorted(list(gamma_id_set))
        # second pass -- parse metrics and file locations
        for name in zf.namelist():
            gamma_id = self._parse_gamma_id(name)
            gamma = gamma_id[0]
            if re.search('_segments\.txt$', name):
                if gamma_id in self.segment_counts:
                    msg = "Multiple aratio_segments.txt for gamma_id {0}".format(gamma_id)
                    self.logger.error(msg)
                    raise SequenzaError(msg)
                self.segment_counts[gamma_id] = self._count_segments(zf.extract(name, tmp))
                self.Aratio_archive[gamma] = name
            elif re.search('_alternative_solutions\.txt$', name) and self._is_primary(gamma_id):
                # alternative_solutions.txt is identical for all solutions; only parse once for each gamma
                self._update_purity_ploidy(gamma, zf.extract(name, tmp))
            elif re.search('_Total_CN.seg', name) and self._is_primary(gamma_id):
                # Only one .seg file for each value of gamma
                if gamma in self.seg_archive:
                    msg = "Multiple .seg files for gamma {0}".format(gamma)
                    self.logger.error(msg)
                    raise SequenzaError(msg)
                self.seg_archive[gamma] = name
        # check required info is present for each gamma_id
        for gamma_id in self.gamma_ids:
            msg = None
            if gamma_id not in self.segment_counts:
                msg = "Missing segment count for gamma_id {0}".format(gamma_id)
            elif gamma_id not in self.purity or gamma_id not in self.ploidy:
                msg = "Missing purity/ploidy for gamma_id {0}".format(gamma_id)
            elif gamma_id[0] not in self.seg_archive:
                msg = "Missing .seg location for gamma {0}".format(gamma_id[0])
            if msg:
                self.logger.error(msg)
                raise SequenzaError(msg)
        tempdir.cleanup()
        # find important values of gamma_id
        [self.default_gamma_id, self.gamma_id_selection_table] = self._find_default_gamma_id()
        [self.min_purity, self.max_purity, self.min_purity_gamma_id, self.max_purity_gamma_id] = self._find_minmax_purity_gamma_id()

    def _construct_gamma_id(self, gamma=None, solution=None):
        """
        Construct a gamma ID from the given gamma and solution (if any), defaults otherwise
        Raise an error if resulting gamma ID is unknown
        """
        self.logger.debug("Constructing gamma ID with inputs gamma={0}, solution={1}".format(gamma, solution))
        if gamma:
            if solution:
                gamma_id = (gamma, solution)
            else:
                gamma_id = (gamma, constants.SEQUENZA_PRIMARY_SOLUTION)
        else:
            gamma_id = self.default_gamma_id
        if gamma_id not in self.gamma_ids:
            msg = "gamma ID {0} not found in '{1}'; ".format(gamma_id, self.zip_path) +\
            "available IDs are: {0}".format(self.gamma_ids)
            self.logger.error(msg)
            raise SequenzaError(msg)
        return gamma_id

    def _count_segments(self, seg_path):
        """Count the number of segments; equal to length of file, excluding the header"""
        with open(seg_path) as seg:
            length = len(seg.readlines())
        return length - 1

    def _find_default_gamma_id(self):
        """
        Gamma heuristic:
        - Only consider the primary (most probable) solution for each gamma
        - Draw a straight line between least and greatest gamma (usually 50 and 2000, respectively),
          to get the "expected gradient"
        - We want to find the transition from steeper-than-linear to shallower-than-linear
        - Compare actual gradient between N-1th and Nth gamma with expected linear gradient
        - (This takes account of non-equal gamma intervals)
        - When actual gradient is less in magnitude than expected gradient, stop and use Nth gamma
        - Return table of working values as a list of lists (may be wanted for output)
        """
        gammas = sorted([g[0] for g in self.gamma_ids if g[1]==constants.SEQUENZA_PRIMARY_SOLUTION])
        gamma_min_id = (gammas[0], constants.SEQUENZA_PRIMARY_SOLUTION)
        gamma_max_id = (gammas[-1], constants.SEQUENZA_PRIMARY_SOLUTION)
        delta_y = self.segment_counts[gamma_max_id] - self.segment_counts[gamma_min_id]
        delta_x = gamma_max_id[0] - gamma_min_id[0]
        linear_gradient = float(delta_y)/delta_x
        chosen_gamma = None
        working_values = []
        # columns for working_values: ['gamma', 'segments', 'gradient', 'expected']
        working_values.append([gamma_min_id[0], self.segment_counts[gamma_min_id], 'NA', 'NA'])
        for i in range(1, len(gammas)):
            gamma_id_now = (gammas[i], constants.SEQUENZA_PRIMARY_SOLUTION)
            gamma_id_previous = (gammas[i-1], constants.SEQUENZA_PRIMARY_SOLUTION)
            delta_y = self.segment_counts[gamma_id_now] - self.segment_counts[gamma_id_previous]
            delta_x = gamma_id_now[0] - gamma_id_previous[0]
            gradient = float(delta_y)/delta_x
            fields = [
                gamma_id_now[0],
                self.segment_counts[gamma_id_now],
                gradient,
                linear_gradient
            ]
            working_values.append(fields)
            if abs(gradient) <= abs(linear_gradient) and chosen_gamma==None:
                chosen_gamma = gamma_id_now
        return (chosen_gamma, working_values)

    def _find_minmax_purity_gamma_id(self):
        """
        Find gamma ID(s) with the minimum and maximum purity values
        """
        min_purity = math.inf
        max_purity = 0
        min_purity_gamma_id = []
        max_purity_gamma_id = []
        for gamma_id in self.gamma_ids:
            purity = self.purity[gamma_id]
            ploidy = self.ploidy[gamma_id]
            if purity > max_purity:
                max_purity = purity
                max_purity_gamma = [gamma_id]
            elif purity == max_purity:
                max_purity_gamma.append(gamma_id)
            if purity < min_purity:
                min_purity = purity
                min_purity_gamma = [gamma_id]
            elif purity == min_purity:
                min_purity_gamma.append(gamma_id)
        return [min_purity, max_purity, min_purity_gamma, max_purity_gamma]

    def _is_primary(self, gamma_id):
        """Does the given gamma_id denote a primary solution?"""
        return gamma_id[1]==constants.SEQUENZA_PRIMARY_SOLUTION

    def _parse_gamma_id(self, name):
        """
        Parse gamma ID from the name of a ZIP archive member.
        ID is a tuple of (gamma, solution identifier).
        The solution identifier is a secondary directory name (eg. 'sol2_0.49') or default value.
        """
        terms = re.split(os.sep, name)
        try:
            gamma = int(terms[1])
            solution = terms[2] if re.match('sol[0-9]_[01](\.[0-9]+)?$', terms[2]) else constants.SEQUENZA_PRIMARY_SOLUTION
            gamma_id = (gamma, solution)
        except (IndexError, ValueError) as err:
            msg = "Unable to parse gamma parameter from {0} ".format(name) +\
                  "in archive {0}".format(self.zip_path)
            self.logger.error(msg)
            raise SequenzaError(msg) from err
        return gamma_id

    def _reformat_metrics(self, metrics):
        """
        Reformat a dictionary of gamma_id -> (purity or ploidy) for JSON output
        Gamma IDs are tuples of (gamma, solution), which are not allowed as keys in JSON
        """
        reformatted = {key[0]:{} for key in metrics.keys()}
        for key in metrics.keys():
            reformatted[key[0]][key[1]] = metrics[key]
        return reformatted

    def _update_purity_ploidy(self, gamma, input_path):
        """
        Update purity and ploidy for the given gamma and alternative_solutions.txt file
        alternative_solutions.txt is identical for all solution folders; contains purity/ploidy solutions for the given gamma
        Non-primary solution names are of the form sol${COUNT}_${PURITY}
        where $COUNT is the line in the alternative_solutions.txt file (header = 0, primary solution = 1)
        Record the purity and ploidy by gamma_id
        """
        count = 0
        with open(input_path, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter="\t")
            for row in reader:
                if count > 0: # ignore the header row
                    [purity, ploidy, slpp] = [float(x) for x in row]
                    if count == 1:
                        solution = constants.SEQUENZA_PRIMARY_SOLUTION
                    elif purity == 1:
                        # annoying quirk of Sequenza output naming
                        solution = "sol{0}_1".format(count)
                    else:
                        solution = "sol{0}_{1}".format(count, purity)
                    gamma_id = self._construct_gamma_id(gamma, solution)
                    self.purity[gamma_id] = purity
                    self.ploidy[gamma_id] = ploidy
                count += 1
        msg = "Found purity & ploidy for gamma={0}, input={1}".format(gamma, input_file)
        self.logger.debug(msg)

    def extract_seg_file(self, dest_dir, gamma=None):
        """
        Extract the Total_CN.seg file; for the supplied gamma (if any), default gamma otherwise.
        No Sequenza solution specified, as .seg file is shared between all solutions for given gamma
        dest_dir is a directory path for the extracted file.
        The .seg file is further processed downstream, before input to singleSample.R
        """
        gamma_id = self._construct_gamma_id(gamma) # supplies defaults and checks validity of gamma
        zf = zipfile.ZipFile(self.zip_path)
        extracted = zf.extract(self.seg_archive[gamma_id[0]], dest_dir)
        return extracted

    def extract_Aratio_file(self, dest_dir, gamma=None, solution=None):
        """
        Extract the aratio_segments.txt file; for the supplied gamma, default gamma otherwise.
        solution must be specified, aratio_segments.txt file is unique to each solution for given gamma
        dest_dir is a directory path for the extracted file.
        The aratio_segments.txt file is further processed downstream, before input to singleSample.R
        """
        gamma_id = self._construct_gamma_id(gamma, solution) # supplies defaults and checks validity of gamma
        zf = zipfile.ZipFile(self.zip_path)
        extracted = zf.extract(self.Aratio_archive[gamma_id[0]], dest_dir)
        return extracted

    def get_default_gamma_id(self):
        return self.default_gamma_id

    def get_purity(self, gamma=None, solution=None):
        """Get purity for supplied gamma and solution (if any), defaults otherwise"""
        gamma_id = self._construct_gamma_id(gamma, solution) # checks gamma_id is valid
        return self.purity[gamma_id]

    def get_ploidy(self, gamma=None, solution=None):
        """Get ploidy for supplied gamma and solution (if any), defaults otherwise"""
        gamma_id = self._construct_gamma_id(gamma, solution) # checks gamma_id is valid
        return self.ploidy[gamma_id]

    def get_segment_counts(self):
        return self.segment_counts

    def print_gamma_selection(self):
        print("Default gamma ID = {0}".format(self.default_gamma_id))
        print("Solution parameters:")
        print("\t".join(['gamma', 'segments', 'gradient', 'expected']))
        for row in self.gamma_id_selection_table:
            print("\t".join([str(x) for x in row]))

    def print_purity_ploidy_table(self):
        print("\t".join(["gamma", "solution", "purity", "ploidy"]))
        for gamma_id in self.gamma_ids:
            row = [gamma_id[0], gamma_id[1], self.purity[gamma_id], self.ploidy[gamma_id]]
            print("\t".join([str(x) for x in row]))

    def print_summary(self):
        print("Minimum purity {0} at:\ngamma\tsolution\tpurity\tploidy".format(self.min_purity))
        for x in self.min_purity_gamma_id:
            print("\t".join([str(y) for y in [x[0], x[1], self.purity[x], self.ploidy[x]]]))
        print('---------------------------------')
        print("Maximum purity {0} at:\ngamma\tsolution\tpurity\tploidy".format(self.max_purity))
        for x in self.max_purity_gamma_id:
            print("\t".join([str(y) for y in [x[0], x[1], self.purity[x], self.ploidy[x]]]))
        print('---------------------------------')
        print("Default gamma ID = {0}".format(self.default_gamma_id))
        print("Purity at default gamma ID = {0}".format(self.purity[self.default_gamma_id]))
        print("Ploidy at default gamma ID = {0}".format(self.ploidy[self.default_gamma_id]))

    def write_json(self, out_path):
        """Write a JSON summary of gamma parameters"""
        params = {
            "default_gamma": self.default_gamma_id,
            "gamma_selection_table": self.gamma_id_selection_table,
            "min_purity": self.min_purity,
            "min_purity_gamma": self.min_purity_gamma_id,
            "max_purity": self.max_purity,
            "max_purity_gamma": self.max_purity_gamma_id,
            "purity": self._reformat_metrics(self.purity),
            "ploidy": self._reformat_metrics(self.ploidy),
            "seg_locations": self.seg_archive,
            "Aratio_locations": self.Aratio_archive
        }
        with open(out_path, 'w') as out_file:
            print(json.dumps(params, sort_keys=True, indent=4), file=out_file)


class SequenzaError(Exception):
    pass
