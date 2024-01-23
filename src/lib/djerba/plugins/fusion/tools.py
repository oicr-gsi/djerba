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
from djerba.util.html import html_builder as hb
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.util.oncokb.annotator import annotator_factory
from djerba.plugins.wgts.tools import wgts_tools
from djerba.util.oncokb.tools import gene_summary_reader
import djerba.plugins.fusion.constants as fc
import djerba.core.constants as core_constants
from djerba.util.subprocess_runner import subprocess_runner

class fusion_reader(logger):

    def __init__(self, input_dir, log_level=logging.WARNING, log_path=None):
        super().__init__()
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.input_dir = input_dir
        fusion_data = self.read_fusion_data()
        annotations = self.read_annotation_data()
        # delly results have been removed from fusion data; also remove delly from annotations
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
        NCCN_fusions = set()
        with open(os.path.join(self.input_dir, fc.DATA_FUSIONS_NCCN_ANNOTATED)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                NCCN_fusions.add(row['Fusion'])
        for fusion_id in fusion_data.keys():
            gene2_exists = True
            if len(fusion_data[fusion_id])==1:
                # skip intragenic fusions, but add to the gene count
                fusion_genes.add(fusion_data[fusion_id][0][fc.HUGO_SYMBOL])
                if fusion_id in NCCN_fusions:
                    self.logger.debug("Fusion {0} rescued by NCCN annotation".format(fusion))
                    gene2_exists = False
                    gene2 = "Intergenic"
                else:
                    intragenic += 1
                    continue
            elif len(fusion_data[fusion_id]) >= 3:
                msg = "More than 2 fusions with the same name: {0}".format(fusion_id)
                self.logger.error(msg)
                raise RuntimeError(msg)
            gene1 = fusion_data[fusion_id][0][fc.HUGO_SYMBOL]
            if gene2_exists:
                gene2 = fusion_data[fusion_id][1][fc.HUGO_SYMBOL]
            fusion_genes.add(gene1)
            fusion_genes.add(gene2)
            frame = fusion_data[fusion_id][0]['Frame']
            translocation = fusion_data[fusion_id][0]['translocation']
            Fusion_newStyle = fusion_data[fusion_id][0]['Fusion_newStyle']
            if gene2_exists:
                for row_input in annotations[fusion_id]:
                    effect = row_input['MUTATION_EFFECT']
                level = oncokb_levels.parse_oncokb_level(row_input)
            else:
                effect = "Undetermined"
                level = "P"
            if level not in ['Unknown', 'NA']:
                if gene2_exists:
                    therapies = oncokb_levels.parse_actionable_therapies(row_input)
                else:
                    therapies = {"P": "Prognostic"}
                fusions.append(
                    fusion(
                        fusion_id,
                        Fusion_newStyle,
                        gene1,
                        gene2,
                        frame,
                        effect,
                        level,
                        therapies,
                        translocation
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

    def build_treatment_entries(self, fusion, therapies, oncotree_code):
        """Make an entry for the treatment options merger"""
        # TODO fix the treatment options merger to display 2 genes for fusions
        genes = fusion.get_genes()
        gene = genes[0]
        factory = tom_factory(self.log_level, self.log_path)
        entries = []
        for level in therapies.keys():
            entry = factory.get_json(
                tier=oncokb_levels.tier(level),
                level=level,
                treatments=therapies[level],
                gene=gene,
                alteration='Fusion',
                alteration_url=hb.build_fusion_url(genes, oncotree_code.lower())
            )
            entries.append(entry)
        return entries

    def fusions_to_json(self, gene_pair_fusions, oncotree_code):
        rows = []
        gene_info = []
        treatment_opts = []
        cytobands = wgts_tools(self.log_level, self.log_path).cytoband_lookup()
        summaries = gene_summary_reader(self.log_level, self.log_path)
        gene_info_factory = gim_factory(self.log_level, self.log_path)
        # table has 2 rows for each oncogenic fusion
        # retain fusions with sort order less than (ie. ahead of) 'Likely Oncogenic'
        maximum_order = oncokb_levels.oncokb_order('P')
        for fusion in gene_pair_fusions:
            oncokb_order = oncokb_levels.oncokb_order(fusion.get_oncokb_level())
            if oncokb_order <= maximum_order:
                for gene in fusion.get_genes():
                    chromosome = cytobands.get(gene)
                    gene_url = hb.build_gene_url(gene)
                    row =  {
                        fc.GENE: gene,
                        fc.GENE_URL: gene_url,
                        fc.CHROMOSOME: chromosome,
                        fc.ONCOKB_LINK: fusion.get_oncokb_link(),
                        fc.FRAME: fusion.get_frame(),
                        fc.TRANSLOCATION: fusion.get_translocation(),
                        fc.FUSION: fusion.get_fusion_id_new(),
                        fc.MUTATION_EFFECT: fusion.get_mutation_effect(),
                        core_constants.ONCOKB: fusion.get_oncokb_level()
                    }
                    rows.append(row)
                    gene_info_entry = gene_info_factory.get_json(
                        gene=gene,
                        summary=summaries.get(gene)
                    )
                    gene_info.append(gene_info_entry)
                    therapies = fusion.get_therapies()
                    for level in therapies.keys():
                        entries = self.build_treatment_entries(
                            fusion,
                            therapies,
                            oncotree_code.lower()
                        )
                        treatment_opts.extend(entries)
        return rows, gene_info, treatment_opts
    
    def get_fusions(self):
        return self.fusions

    def get_total_fusion_genes(self):
        return self.total_fusion_genes
 
    def read_annotation_data(self):
        # annotation file has exactly 1 line per fusion
        annotations_by_fusion = {}
        with open(os.path.join(self.input_dir, fc.DATA_FUSIONS_ANNOTATED)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                fusion = row['Fusion']
                if fusion in annotations_by_fusion:
                    annotations_by_fusion[fusion].append(row)
                else:
                    annotations_by_fusion[fusion] = [row,]
        with open(os.path.join(self.input_dir, fc.DATA_FUSIONS_NCCN_ANNOTATED)) as data_file:
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
        with open(os.path.join(self.input_dir, fc.DATA_FUSIONS_OLD)) as data_file:
            delly_count = 0
            total = 0
            for row in csv.DictReader(data_file, delimiter="\t"):
                total += 1
                if row['Method']=='delly':
                    # omit delly structural variants (which are not yet validated)
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

class prepare_fusions(logger):

    def __init__(self, input_dir, log_level=logging.WARNING, log_path=None):
        super().__init__()
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.input_dir = input_dir

    def annotate_fusion_files(self, config_wrapper):
        # annotate from OncoKB
        # TODO check if fusions are non empty
        factory = annotator_factory(self.log_level, self.log_path)
        factory.get_annotator(self.input_dir, config_wrapper).annotate_fusion()

    def process_fusion_files(self, config_wrapper):
        """
        Preprocess fusion inputs and run R scripts; write outputs to the workspace
        Inputs assumed to be in Mavis .tab format; .zip format is no longer in use
        """
        mavis_path = config_wrapper.get_my_string(fc.MAVIS_PATH)
        arriba_path = config_wrapper.get_my_string(fc.ARRIBA_PATH)
        tumour_id = config_wrapper.get_my_string(core_constants.TUMOUR_ID)
        oncotree = config_wrapper.get_my_string(fc.ONCOTREE_CODE)
        oncotree = oncotree.upper()
        entrez_conv_path = config_wrapper.get_my_string(fc.ENTREZ_CONVERSION_PATH)
        min_reads = config_wrapper.get_my_int(fc.MIN_FUSION_READS)
        fus_path = os.path.join(self.input_dir, 'fus.txt') 
        self.logger.info("Processing fusion results from " + mavis_path)
        # prepend a column with the tumour ID to the Mavis .tab output
        with open(mavis_path, 'rt') as in_file, open(fus_path, 'wt') as out_file:
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            in_header = True
            for row in reader:
                if in_header:
                    value = 'Sample'
                    in_header = False
                else:
                    value = tumour_id
                new_row = [value] + row
                writer.writerow(new_row)
        # run the R script
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.join(plugin_dir, 'fusions.R')
        cmd = [
            'Rscript', script_path,
            '--entcon', entrez_conv_path,
            '--fusfile', fus_path,
            '--arriba', arriba_path,
            '--minfusionreads', min_reads,
            '--workdir', self.input_dir,
            '--oncotree', oncotree
        ]
        subprocess_runner(self.log_level, self.log_path).run([str(x) for x in cmd])
        self.annotate_fusion_files(config_wrapper)
        self.logger.info("Finished writing fusion files")

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
            therapies,
            translocation
    ):
        self.fusion_id_old = fusion_id_old
        self.fusion_id_new = fusion_id_new
        self.gene1 = gene1
        self.gene2 = gene2
        self.frame = frame
        self.translocation = translocation
        self.effect = effect
        self.therapies = therapies
        self.level = level

    def get_fusion_id_old(self):
        return self.fusion_id_old

    def get_fusion_id_new(self):
        return self.fusion_id_new

    def get_genes(self):
        return [self.gene1, self.gene2]

    def get_translocation(self):
        return self.translocation

    def get_frame(self):
        return self.frame

    def get_oncokb_link(self):
        gene1_url = hb.build_gene_url(self.gene1)
        gene1_and_url = hb.href(gene1_url, self.gene1)
        gene2_url = hb.build_gene_url(self.gene2)
        gene2_and_url = hb.href(gene2_url, self.gene2)
        return("::".join((gene1_and_url, gene2_and_url)))

    def get_oncokb_level(self):
        return self.level

    def get_mutation_effect(self):
        return self.effect

    def get_fda_level(self):
        return self.fda_level

    def get_therapies(self):
        return self.therapies





