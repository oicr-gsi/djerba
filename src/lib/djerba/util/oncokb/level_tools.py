"""Simple functions to process OncoKB levels"""

import re
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb

def is_null_string(value):
    if isinstance(value, str):
        return value in ['', 'NA']
    else:
        msg = "Invalid argument to is_null_string(): '{0}' of type '{1}'".format(value, type(value))
        raise RuntimeError(msg)

def oncokb_filter(row):
    """True if level passes filter, ie. if row should be kept"""
    likely_oncogenic_sort_order = oncokb_order('N2')
    return oncokb_order(row.get(core_constants.ONCOKB)) <= likely_oncogenic_sort_order

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

def oncokb_order(level):
    levels = ['1', '2', '3A', '3B', '4', 'R1', 'R2', 'N1', 'N2', 'N3', 'Unknown']
    order = None
    for i in range(len(levels)):
        if str(level) == levels[i]:
            order = i
            break
    if order == None:
        raise RuntimeError("Unknown OncoKB level: {0}".format(level))
    return order

def parse_max_oncokb_level_and_therapies(row_dict, levels):
    # find maximum level (if any) from given levels list, and associated therapies
    max_level = None
    therapies = []
    for level in levels:
        if not is_null_string(row_dict[level]):
            if not max_level: max_level = level
            therapies.append(row_dict[level])
    if max_level:
        max_level = reformat_level_string(max_level)
    # insert a space between comma and start of next word
    therapies = [re.sub(r'(?<=[,])(?=[^\s])', r' ', t) for t in therapies]
    return (max_level, '; '.join(therapies))

def parse_oncokb_level(row_dict):
    # find oncokb level string: eg. "Level 1", "Likely Oncogenic", "None"
    max_level = None
    for level in oncokb.THERAPY_LEVELS:
        if not is_null_string(row_dict[level]):
            max_level = level
            break
    if max_level:
        parsed_level = reformat_level_string(max_level)
    elif not is_null_string(row_dict[oncokb.ONCOGENIC_UC]):
        parsed_level = row_dict[oncokb.ONCOGENIC_UC]
    else:
        parsed_level = 'NA'
    return parsed_level

def reformat_level_string(level):
    return re.sub('LEVEL_', 'Level ', level)
