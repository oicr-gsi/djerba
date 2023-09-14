"""
Plugin to generate the Fusions report section
"""

import csv
import logging
import os
import re
from djerba.plugins.base import plugin_base, DjerbaPluginError
from djerba.util.html import html_builder as hb
from djerba.util.logger import logger
from djerba.util.render_mako import mako_renderer
from djerba.util.subprocess_runner import subprocess_runner
import djerba.core.constants as core_constants
import djerba.util.oncokb.level_tools

class main(plugin_base):

    PRIORITY = 400
    PLUGIN_VERSION = '1.0.0'
    MAKO_TEMPLATE_NAME = 'fusion_template.html'

    # INI config keys
    MAVIS_PATH = 'mavis path'
    ENTREZ_CONVERSION_PATH = 'entrez conv path'
    MIN_FUSION_READS = 'minimum fusion reads'
    
    # JSON results keys
    TOTAL_VARIANTS = "Total variants"
    CLINICALLY_RELEVANT_VARIANTS = "Clinically relevant variants"
    BODY = 'body'
    GENE = 'gene'
    GENE_URL = 'gene URL'
    CHROMOSOME = 'chromosome'
    FUSION = 'fusion'
    MUTATION_EFFECT = 'mutation effect'
    # ONCOKB is from core constants

    # other constants
    ENTRCON_NAME = 'entrez_conversion.txt'

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        data_dir = os.environ.get(core_constants.DJERBA_DATA_DIR_VAR)
        if wrapper.my_param_is_null(self.ENTREZ_CONVERSION_PATH):
            enscon_path = os.path.join(data_dir, self.ENTRCON_NAME)
            wrapper.set_my_param(self.ENTREZ_CONVERSION_PATH, enscon_path)
        if wrapper.my_param_is_null(self.MAVIS_PATH):
            path_info = self.workspace.read_json(core_constants.DEFAULT_PATH_INFO)
            mavis_path = path_info.get('mavis')
            if mavis_path == None:
                msg = 'Cannot find Mavis path for fusion input'
                self.logger.error(msg)
                raise RuntimeError(msg)
            wrapper.set_my_param(self.MAVIS_PATH, mavis_path)
        if wrapper.my_param_is_null(core_constants.TUMOUR_ID):
            sample_info = self.workspace.read_json(core_constants.DEFAULT_SAMPLE_INFO)
            tumour_id = sample_info.get(core_constants.TUMOUR_ID)
            wrapper.set_my_param(core_constants.TUMOUR_ID, tumour_id)
        return wrapper.get_config()

    def cytoband_lookup(self):
        data_dir = os.environ.get(core_constants.DJERBA_DATA_DIR_VAR)
        cytoband_path = os.path.join(data_dir, 'cytoBand.txt')
        cytobands = {}
        with open(cytoband_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                cytobands[row['Hugo_Symbol']] = row['Chromosome']
        return cytobands

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        self.process_fusion_files(
            wrapper.get_my_string(self.MAVIS_PATH),
            wrapper.get_my_string(core_constants.TUMOUR_ID),
            wrapper.get_my_string(self.ENTREZ_CONVERSION_PATH),
            wrapper.get_my_int(self.MIN_FUSION_READS)
        )
        self.annotate_fusion_files()
        cytobands = self.cytoband_lookup()
        fus_reader = fusion_reader(
            self.workspace.get_work_dir(), self.log_level, self.log_path
        )
        total_fusion_genes = fus_reader.get_total_fusion_genes()
        gene_pair_fusions = fus_reader.get_fusions()
        if gene_pair_fusions is not None:
            # table has 2 rows for each oncogenic fusion
            rows = []
            for fusion in self.gene_pair_fusions:
                oncokb_level = fusion.get_oncokb_level()
                for gene in fusion.get_genes():
                    row =  {
                        self.GENE: gene,
                        self.GENE_URL: hb.build_gene_url(gene),
                        self.CHROMOSOME: cytobands.get(gene),
                        self.FRAME: fusion.get_frame(),
                        self.FUSION: fusion.get_fusion_id_new(),
                        self.MUTATION_EFFECT: fusion.get_mutation_effect(),
                        core_constants.ONCOKB: oncokb_level
                    }
                    rows.append(row)
            # rows are already sorted by the fusion reader
            rows = list(filter(level_tools.oncokb_filter, rows))
            distinct_oncogenic_genes = len(set([row.get(self.GENE) for row in rows]))
            results = {
                self.TOTAL_VARIANTS: distinct_oncogenic_genes,
                self.CLINICALLY_RELEVANT_VARIANTS: total_fusion_genes,
                self.BODY: rows
            }
        else:
            results = {
                self.TOTAL_VARIANTS: 0,
                self.CLINICALLY_RELEVANT_VARIANTS: 0,
                self.BODY: []
            }
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        data[core_constants.RESULTS] = results
        return data

    def process_fusion_files(self, mavis_path, tumour_id, entrez_conv_path, min_reads):
        """
        Preprocess fusion inputs and run R scripts; write outputs to the workspace
        Inputs assumed to be in Mavis .tab format; .zip format is no longer in use
        """
        fus_path = self.workspace.abs_path('fus.txt')
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
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        script_path = os.path.join(plugin_dir, 'fusions.R')
        cmd = [
            'Rscript', script_path,
            '--entcon', entrez_conv_path,
            '--fusfile', fus_path,
            '--minfusionreads', min_reads,
            '--outdir', os.path.abspath(self.workspace.get_work_dir())
        ]
        subprocess_runner(self.log_level, self.log_path).run([str(x) for x in cmd])

    def specify_params(self):
        self.add_ini_discovered(self.ENTREZ_CONVERSION_PATH)
        self.add_ini_discovered(self.MAVIS_PATH)
        self.add_ini_discovered(core_constants.TUMOUR_ID)
        self.set_ini_default(self.MIN_FUSION_READS, 20)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.MAKO_TEMPLATE_NAME, data)


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
        # sort the fusions by oncokb level & fusion ID
        fusions = sorted(fusions, key=lambda f: f.get_fusion_id_new())
        self.fusions = sorted(fusions, key=lambda f: self.oncokb_sort_order(f.get_oncokb_level()))

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
            ann = annotations[fusion_id]
            effect = ann['MUTATION_EFFECT']
            oncokb_level = self.parse_oncokb_level(ann)
            fda = self.parse_max_oncokb_level_and_therapies(ann, oncokb.FDA_APPROVED_LEVELS)
            [fda_level, fda_therapies] = fda
            inv = self.parse_max_oncokb_level_and_therapies(ann, oncokb.INVESTIGATIONAL_LEVELS)
            [inv_level, inv_therapies] = inv
            fusions.append(
                fusion(
                    fusion_id,
                    self.old_to_new_delimiter[fusion_id],
                    gene1,
                    gene2,
                    frame,
                    effect,
                    oncokb_level,
                    fda_level,
                    fda_therapies,
                    inv_level,
                    inv_therapies
                )
            )
        total = len(fusions)
        total_fusion_genes = len(fusion_genes)
        msg = "Finished collating fusion table data. "+\
              "Found {0} fusion rows for {1} distinct genes; ".format(total, total_fusion_genes)+\
              "excluded {0} intragenic rows.".format(intragenic)
        self.logger.info(msg)
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
                annotations_by_fusion[row['Fusion']] = row
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
            oncokb_level,
            fda_level,
            fda_therapies,
            inv_level,
            inv_therapies
    ):
        self.fusion_id_old = fusion_id_old
        self.fusion_id_new = fusion_id_new
        self.gene1 = gene1
        self.gene2 = gene2
        self.frame = frame
        self.effect = effect
        self.oncokb_level = oncokb_level
        self.fda_level = fda_level
        self.fda_therapies = fda_therapies
        self.inv_level = inv_level
        self.inv_therapies = inv_therapies

    def get_fusion_id_old(self):
        return self.fusion_id_old

    def get_fusion_id_new(self):
        return self.fusion_id_new

    def get_genes(self):
        return [self.gene1, self.gene2]

    def get_frame(self):
        return self.frame

    def get_mutation_effect(self):
        return self.effect

    def get_oncokb_level(self):
        return self.oncokb_level

    def get_fda_level(self):
        return self.fda_level

    def get_fda_therapies(self):
        return self.fda_therapies

    def get_inv_level(self):
        return self.inv_level

    def get_inv_therapies(self):
        return self.inv_therapies



