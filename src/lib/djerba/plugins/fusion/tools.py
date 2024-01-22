"""
Utility classes for the fusions plugin
"""

import csv
import logging
import os
import re
from djerba.util.logger import logger
from djerba.util.oncokb.tools import levels as oncokb_levels
import djerba.util.oncokb.constants as oncokb

class fusion_reader(logger):

    # read files from an input directory and gather information on fusions
    DATA_FUSIONS_NEW = 'data_fusions_new_delimiter.txt'
    DATA_FUSIONS_OLD = 'data_fusions.txt'
    DATA_FUSIONS_ANNOTATED = 'data_fusions_oncokb_annotated.txt'
    FUSION_INDEX = 4
    HUGO_SYMBOL = 'Hugo_Symbol'

    def __init__(self, input_dir, log_level=logging.WARNING, log_path=None):
        super().__init__()
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.input_dir = input_dir
        self.old_to_new_delimiter = self.read_fusion_delimiter_map()
        fusion_data = self.read_fusion_data()
        annotations = self.read_annotation_data()
        # delly results have been removed from fusion data; do the same for annotations
        for key in [k for k in annotations.keys() if k not in fusion_data]:
            del annotations[key]
        # now check the key sets match
        if set(fusion_data.keys()) != set(annotations.keys()):
            msg = "Distinct fusion identifiers and annotations do not match. "+\
                  "Fusion data: {0}; ".format(sorted(list(set(fusion_data.keys()))))+\
                  "Annotations: {0}".format(sorted(list(set(annotations.keys()))))
            self.logger.error(msg)
            raise RuntimeError(msg)
        [fusions, self.total_fusion_genes] = self._collate_row_data(fusion_data, annotations)
        # sort the fusions by fusion ID
        self.fusions = sorted(fusions, key=lambda f: f.get_fusion_id_new())
        

    def _collate_row_data(self, fusion_data, annotations):
        fusions = []
        fusion_genes = set()
        self.logger.debug("Starting to collate fusion table data.")
        intragenic = 0
        for fusion_id in fusion_data.keys():
            if len(fusion_data[fusion_id])==1:
                # add intragenic fusions to the gene count, then skip
                fusion_genes.add(fusion_data[fusion_id][0][self.HUGO_SYMBOL])
                intragenic += 1
                continue
            elif len(fusion_data[fusion_id]) >= 3:
                msg = "More than 2 fusions with the same name: {0}".format(fusion_id)
                self.logger.error(msg)
                raise RuntimeError(msg)
            gene1 = fusion_data[fusion_id][0][self.HUGO_SYMBOL]
            gene2 = fusion_data[fusion_id][1][self.HUGO_SYMBOL]
            fusion_genes.add(gene1)
            fusion_genes.add(gene2)
            frame = fusion_data[fusion_id][0]['Frame']
            for row_input in annotations[fusion_id]:
                effect = row_input['MUTATION_EFFECT']
            level = oncokb_levels.parse_oncokb_level(row_input)
            print(level)
            if level not in ['Unknown', 'NA']:
                therapies = oncokb_levels.parse_actionable_therapies(row_input)
                fusions.append(
                    fusion(
                        fusion_id,
                        self.old_to_new_delimiter[fusion_id],
                        gene1,
                        gene2,
                        frame,
                        effect,
                        level,
                        therapies
                    )
                )
        total = len(fusions)
        total_fusion_genes = len(fusion_genes)
        msg = "Finished collating fusion table data. "+\
              "Found {0} fusion rows for {1} distinct genes; ".format(total, total_fusion_genes)+\
              "excluded {0} intragenic rows.".format(intragenic)
        self.logger.info(msg)
        for fusion_row in fusions:
            self.logger.debug("Fusions: {0}".format(fusion_row.get_genes()))
        return [fusions, total_fusion_genes]

    def get_fusions(self):
        return self.fusions

    def get_total_fusion_genes(self):
        return self.total_fusion_genes

    def read_annotation_data(self):
        # annotation file has exactly 1 line per fusion
        annotations_by_fusion = {}
        with open(os.path.join(self.input_dir, self.DATA_FUSIONS_ANNOTATED)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                fusion = row['Fusion']
                if fusion in annotations_by_fusion:
                    annotations_by_fusion[fusion].append(row)
                else:
                    annotations_by_fusion[fusion] = [row,]
        return annotations_by_fusion

    def read_fusion_data(self):
        # data file has 1 or 2 lines per fusion (1 if it has an intragenic component, 2 otherwise)
        data_by_fusion = {}
        with open(os.path.join(self.input_dir, self.DATA_FUSIONS_OLD)) as data_file:
            delly_count = 0
            total = 0
            for row in csv.DictReader(data_file, delimiter="\t"):
                total += 1
                if row['Method']=='delly':
                    # omit delly structural variants (which are not fusions, and not yet validated)
                    delly_count += 1
                else:
                    # make fusion ID consistent with format in annotated file
                    fusion_id = re.sub('None', 'intragenic', row['Fusion'])
                    if fusion_id in data_by_fusion:
                        data_by_fusion[fusion_id].append(row)
                    else:
                        data_by_fusion[fusion_id] = [row,]
        self.logger.debug("Read {0} rows of fusion input; excluded {1} delly rows".format(total, delly_count))
        return data_by_fusion

    def read_fusion_delimiter_map(self):
        # read the mapping of fusion identifiers from old - to new :: delimiter
        # ugly workaround implemented in upstream R script; TODO refactor to something neater
        with open(os.path.join(self.input_dir, self.DATA_FUSIONS_OLD)) as file_old:
            old = [row[self.FUSION_INDEX] for row in csv.reader(file_old, delimiter="\t")]
        with open(os.path.join(self.input_dir, self.DATA_FUSIONS_NEW)) as file_new:
            new = [row[self.FUSION_INDEX] for row in csv.reader(file_new, delimiter="\t")]
        if len(old) != len(new):
            msg = "Fusion ID lists from {0} are of unequal length".format(report_dir)
            self.logger.error(msg)
            raise RuntimeError(msg)
        # first item of each list is the header, which can be ignored
        return {old[i]:new[i] for i in range(1, len(old))}

class fusion:
    # container for data relevant to reporting a fusion

    def __init__(
            self,
            fusion_id_old,
            fusion_id_new,
            gene1,
            gene2,
            frame,
            effect,
            level,
            therapies
    ):
        self.fusion_id_old = fusion_id_old
        self.fusion_id_new = fusion_id_new
        self.gene1 = gene1
        self.gene2 = gene2
        self.frame = frame
        self.effect = effect
        self.therapies = therapies
        self.level = level

    def get_fusion_id_old(self):
        return self.fusion_id_old

    def get_fusion_id_new(self):
        return self.fusion_id_new

    def get_genes(self):
        return [self.gene1, self.gene2]

    def get_frame(self):
        return self.frame

    def get_oncokb_level(self):
        return self.level

    def get_mutation_effect(self):
        return self.effect

    def get_fda_level(self):
        return self.fda_level

    def get_therapies(self):
        return self.therapies



