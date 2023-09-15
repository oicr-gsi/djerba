"""Simple functions to process actionability tiers and other information from OncoKB"""

import csv
import os
import re
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb

class levels:

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
        levels = ['1', '2', '3A', '3B', '4', 'R1', 'R2', 'N1', 'N2', 'N3', 'Unknown']
        order = None
        for i in range(len(levels)):
            if str(level) == levels[i]:
                order = i
                break
        if order == None:
            raise RuntimeError("Unknown OncoKB level: {0}".format(level))
        return order

    @staticmethod
    def parse_max_oncokb_level_and_therapies(row_dict, levels_list):
        # find maximum level (if any) from given levels list, and associated therapies
        max_level = None
        therapies = []
        for level in levels_list:
            if not levels.is_null_string(row_dict[level]):
                if not max_level: max_level = level
                therapies.append(row_dict[level])
        if max_level:
            max_level = levels.reformat_level_string(max_level)
        # insert a space between comma and start of next word
        therapies = [re.sub(r'(?<=[,])(?=[^\s])', r' ', t) for t in therapies]
        return (max_level, '; '.join(therapies))

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
        elif not is_null_string(row_dict[oncokb.ONCOGENIC_UC]):
            parsed_level = row_dict[oncokb.ONCOGENIC_UC]
        else:
            parsed_level = 'NA'
        return parsed_level

    @staticmethod
    def reformat_level_string(level):
        return re.sub('LEVEL_', 'Level ', level)


class gene_summary_reader:

    DEFAULT = 'OncoKB summary not available'

    def __init__(self):
        self.summaries = {}
        data_dir = os.environ.get(core_constants.DJERBA_DATA_DIR_VAR)
        with open(os.path.join(data_dir, oncokb.ALL_CURATED_GENES)) as in_file:
            for row in csv.DictReader(in_file, delimiter="\t"):
                self.summaries[row['hugoSymbol']] = row['summary']

    def get(self, gene):
        return self.summaries.get(gene, self.DEFAULT)
