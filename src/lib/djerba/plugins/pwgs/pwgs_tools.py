"""pwgs supporting functions"""
import csv
from decimal import Decimal
import logging
import re

import djerba.plugins.pwgs.constants as constants
import djerba.util.provenance_index as index
        
def preprocess_results(self, results_path):
    '''Pulls key result numbers from result file output from default mrdetect run'''
    results_dict = {}
    with open(results_path, 'r') as results_file:
        reader_file = csv.reader(results_file, delimiter="\t")
        next(reader_file, None)
        for row in reader_file:
            try:
                results_dict = {
                    constants.TUMOUR_FRACTION_ZVIRAN: float('%.1E' % Decimal(row[7])) * 100,
                    constants.PVALUE: float('%.3E' % Decimal(row[10])),
                    constants.DATASET_DETECTION_CUTOFF: float(row[11])
                }
            except IndexError as err:
                msg = "Incorrect number of columns in vaf row: '{0}' ".format(row) + \
                      "read from '{0}'".format(results_path)
                raise RuntimeError(msg) from err

    p_value = results_dict[constants.PVALUE]
    detection_cutoff = results_dict[constants.DATASET_DETECTION_CUTOFF]
    tumour_fraction = results_dict[constants.TUMOUR_FRACTION_ZVIRAN]

    if p_value > float(constants.DETECTION_ALPHA):
        if tumour_fraction > detection_cutoff:
            significance_text = "Statistically insignificant p-value but meets the tumour fraction cutoff."
            results_dict[constants.CTDNA_OUTCOME] = "DETECTED"
        else:
            significance_text = "Not Statistically significant and does not meet the tumour fraction cutoff."
            results_dict[constants.CTDNA_OUTCOME] = "UNDETECTED"
        #results_dict[constants.TUMOUR_FRACTION_ZVIRAN] = 0
    elif p_value <= float(constants.DETECTION_ALPHA):
        if tumour_fraction > detection_cutoff:
            significance_text = "Statistically significant."
            results_dict[constants.CTDNA_OUTCOME] = "DETECTED"
        else:
            significance_text = "Statistically significant p-value but does not meet the tumour fraction cutoff."
            results_dict[constants.CTDNA_OUTCOME] = "UNDETECTED"
    else:
        msg = "results pvalue {0} incompatible with detection alpha {1}".format(p_value, constants.DETECTION_ALPHA)
        self.logger.error(msg)
        raise RuntimeError

    results_dict[constants.SIGNIFICANCE] = significance_text
    return results_dict

