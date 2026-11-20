"""Methods to generate SNV/indel html"""

import djerba.core.constants as core_constants
import djerba.plugins.mrd_wisp.constants as constants
from djerba.util.html import html_builder as hb

class wisp_table_builder:

    @classmethod
    def make_header(klass):
        names = [
            'Timepoint',
            'Detection\nStatus',
            'Tumour Fraction (%)',
            'Allele Fragments'
        ]
        return hb.thead(names)

    @classmethod
    def make_rows(klass, results):
        samples = results[constants.WISP_TABLE_DATA]
        rows = []
        
        for sample in samples:
            detection = sample[constants.WISP_DETECTION]
            if detection == "Detected":
                x = '<td style="color: red; font-weight: bold;">{0}</td>'.format(detection)
            else:
                x = hb.td(detection)
            cells = [
                hb.td(sample[constants.TIMEPOINT]),
                x,
                #hb.td(sample[constants.WISP_DETECTION]),
                hb.td(sample[constants.WISP_TF]),
                hb.td(sample[constants.WISP_AF])
            ]
            rows.append(hb.tr(cells))
        return rows[::-1]
