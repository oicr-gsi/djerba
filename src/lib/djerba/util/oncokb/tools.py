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

    ACTIONABLE_LEVELS = ['1', '2', '3A', '3B', '4', 'R1', 'R2']
    REPORTABLE_LEVELS = ['1', '2', '3A', '3B', '4', 'R1', 'R2', 'N1', 'N2']
    ALL_LEVELS = ['1', '2', '3A', '3B', '4', 'R1', 'R2', 'N1', 'N2', 'N3', 'N4', 'Unknown']

    @staticmethod
    def is_null_string(value):
        if isinstance(value, str):
            return value in ['', 'NA']
        else:
            msg = "Invalid argument to is_null_string(): '{0}' of type '{1}'".format(value, type(value))
            raise RuntimeError(msg)

    @staticmethod
    def oncokb_filter(row):
        """True if level passes filter, ie. if row should be kept"""
        likely_oncogenic_order = levels.oncokb_order('N2')
        return levels.oncokb_order(row.get(core_constants.ONCOKB)) <= likely_oncogenic_order

    @staticmethod
    def oncokb_filter_actionable(row):
        """True if level passes filter, ie. if row should be kept"""
        actionable_order = levels.oncokb_order('R2')
        return levels.oncokb_order(row.get(core_constants.ONCOKB)) <= actionable_order

    @staticmethod
    def oncokb_level_to_html(level):
        if level == "1" or level == 1:
            html = '<div class="circle oncokb-level1">1</div>'
        elif level == "2" or level == 2:
            html = '<div class="circle oncokb-level2">2</div>'
        elif level == "3A":
            html = '<div class="circle oncokb-level3A">3A</div>'
        elif level == "3B":
            html = '<div class="circle oncokb-level3B">3B</div>'
        elif level == "4":
            html = '<div class="circle oncokb-level4">4</div>'
        elif level == "R1":
            html = '<div class="circle oncokb-levelR1">R1</div>'
        elif level == "R2":
            html = '<div class="circle oncokb-levelR2">R2</div>'
        elif level == "N1":
            html = '<div class="square oncokb-levelN1">N1</div>'
        elif level == "N2":
            html = '<div class="square oncokb-levelN2">N2</div>'
        elif level == "N3":
            html = '<div class="square oncokb-levelN3">N3</div>'
        else:
            raise RuntimeError("Unknown OncoKB level: '{0}'".format(level))
        return html

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
            raise RuntimeError("Unknown OncoKB level: {0}".format(level))
        return order

    @staticmethod
    def parse_max_actionable_level_and_therapies(row_dict):
        return levels.parse_max_oncokb_level_and_therapies(
            row_dict,
            levels.ACTIONABLE_LEVELS
        )

    @staticmethod
    def parse_max_oncokb_level_and_therapies(row_dict, levels_list):
        # find maximum level (if any) from given levels list, and associated therapies
        max_level = None
        therapies = []
        # row_dict has keys of the form 'LEVEL_1'; corresponding levels_list entry is '1'
        for key in row_dict.keys():
            level = levels.reformat_level_string(key)
            if level in levels_list and not levels.is_null_string(row_dict[key]):
                if not max_level:
                    max_level = level
                therapies.append(row_dict[key])
        # insert a space between comma and start of next word
        therapies = [re.sub(r'(?<=[,])(?=[^\s])', r' ', t) for t in therapies]
        return (max_level, '; '.join(therapies))

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
        for level in oncokb.THERAPY_LEVELS:
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
        else:
            tier = None
        return tier

class gene_summary_reader(logger):

    DEFAULT = 'OncoKB summary not available'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.summaries = {}
        data_dir = directory_finder(log_level, log_path).get_data_dir()
        with open(os.path.join(data_dir, oncokb.ALL_CURATED_GENES)) as in_file:
            for row in csv.DictReader(in_file, delimiter="\t"):
                self.summaries[row['hugoSymbol']] = row['summary']

    def get(self, gene):
        return self.summaries.get(gene, self.DEFAULT)
