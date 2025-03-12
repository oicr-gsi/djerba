"""Simple functions to process actionability tiers and other information from OncoKB"""

import csv
import logging
import os
import re
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb
from djerba.util.environment import directory_finder
from djerba.util.logger import logger

class levels:

    ALTERNATE_LEVEL_KEY = 'OncoKB level' #  used in TAR SNV/indel
    ACTIONABLE_LEVELS = ['1', '2', '3A', '3B', '4', 'R1', 'R2', 'P']
    REPORTABLE_LEVELS = ACTIONABLE_LEVELS+['N1', 'N2']
    ALL_LEVELS = ['1', '2', '3A', '3B', '4', 'R1', 'R2', 'N1', 'N2', 'N3', 'N4', 'P', 'Unknown']

    @staticmethod
    def filter_reportable(rows):
        # return a list of rows which are reportable
        # TODO refactor the TAR SNV/indel plugin to use core constant
        if len(rows)==0:
            return rows
        elif core_constants.ONCOKB in rows[0]:
            level_key = core_constants.ONCOKB
        elif levels.ALTERNATE_LEVEL_KEY in rows[0]:
            level_key = levels.ALTERNATE_LEVEL_KEY
        else:
            msg = "No OncoKB level key in filter input: {0}".format(rows[0])
            raise MissingOncokbLevelError(msg)
        rows = filter(lambda x: levels.is_reportable(x[level_key]), rows)
        return list(rows)

    @staticmethod
    def is_null_string(value):
        if isinstance(value, str):
            return value in ['', 'NA']
        else:
            msg = "Invalid argument to is_null_string(): '{0}' of type '{1}'".format(value, type(value))
            raise ValueError(msg)

    @staticmethod
    def is_actionable(level):
        return level in levels.ACTIONABLE_LEVELS

    @staticmethod
    def is_reportable(level):
        return level in levels.REPORTABLE_LEVELS

    @staticmethod
    def oncokb_level_to_html(level):
        if level in ['1', '2', '3A', '3B', '4', 'R1', 'R2']:
            shape = 'circle'
        elif level in ['N1', 'N2', 'N3', 'P']:
            shape = 'square'
        elif level == 'N4':
            shape = 'square-dark-text'
        else:
            raise UnrecognizedOncokbLevelError("Unrecognized OncoKB level: {0}".format(level))
        div = '<div class="{0} oncokb-level{1}">{1}</div>'.format(shape, level)
        return div

    @staticmethod
    def oncokb_order(level):
        if re.match('Level ', level):
            level = level.replace('Level ', '')
        order = None
        for i in range(len(levels.ALL_LEVELS)):
            if str(level) == levels.ALL_LEVELS[i]:
                order = i
                break
        if order == None:
            raise UnrecognizedOncokbLevelError("Unrecognized OncoKB level: {0}".format(level))
        return order

    @staticmethod
    def parse_strongest_level(input_levels):
        """Level 1 is "stronger" than level 2 despite having a lower number, etc. """
        strongest = 'Unknown'
        for level in levels.ALL_LEVELS:
            if level in input_levels:
                strongest = level
                break
        return strongest

    @staticmethod
    def parse_actionable_therapies(row_dict):
        return levels.parse_oncokb_therapies(
            row_dict,
            levels.ACTIONABLE_LEVELS
        )

    @staticmethod
    def parse_oncokb_therapies(row_dict, levels_list):
        # find maximum level (if any) from given levels list, and associated therapies
        # return a dictionary of the form LEVEL->THERAPIES, also record the max level
        therapies = {}
        # row_dict has keys of the form 'LEVEL_1'; corresponding levels_list entry is '1'
        for key in row_dict.keys():
            level = levels.reformat_level_string(key)
            if level in levels_list and not levels.is_null_string(row_dict[key]):
                # insert a space between comma and start of next word
                therapy = re.sub(r'(?<=[,])(?=[^\s])', r' ', row_dict[key])
                therapies[level] = therapy
        return therapies

    @staticmethod
    def parse_oncokb_level(row_dict):
        # find oncokb level string: eg. "Level 1", "Likely Oncogenic", "None"
        max_level = None
        for level in oncokb.ANNOTATION_THERAPY_LEVELS:
            if not levels.is_null_string(row_dict[level]):
                max_level = level
                break
        if max_level:
            parsed_level = levels.reformat_level_string(max_level)
        elif not levels.is_null_string(row_dict[oncokb.ONCOGENIC_UC]):
            parsed_level = levels.reformat_level_string(row_dict[oncokb.ONCOGENIC_UC])
        else:
            parsed_level = 'NA'
        return parsed_level

    @staticmethod
    def reformat_level_string(level):
        unknown = 'Unknown'
        if level == 'Oncogenic':
            reformatted = 'N1'
        elif level == 'Likely Oncogenic':
            reformatted = 'N2'
        elif level == 'Predicted Oncogenic':
            reformatted = 'N3'
        elif level == 'Likely Neutral' or level == 'Inconclusive':
            reformatted = 'N4'
        elif level == unknown:
            reformatted = unknown
        else:
            reformatted = re.sub('LEVEL_', '', level)
        return reformatted

    @staticmethod
    def tier(level):
        if level in ['1', '2', 'R1']:
            tier = "Approved"
        elif level in ['3A', '3B', '4', 'R2']:
            tier = "Investigational"
        elif level in ['P']:
            tier = "Prognostic"
        else:
            tier = None
        return tier

class gene_summary_reader(logger):

    DEFAULT = 'OncoKB summary not available'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.summaries = {}
        oncokb_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(oncokb_dir, oncokb.ALL_CURATED_GENES)) as in_file:
            for row in csv.DictReader(in_file, delimiter="\t"):
                self.summaries[row['hugoSymbol']] = row['summary']

    def get(self, gene):
        return self.summaries.get(gene, self.DEFAULT)

class UnrecognizedOncokbLevelError(Exception):
    pass

class MissingOncokbLevelError(Exception):
    pass
