"""
Supporting tools for the CNV plugin
"""

import csv
import json
import logging
import os
import djerba.core.constants as core_constants
import djerba.plugins.wgts.cnv_purple.legacy_constants as cnv
import djerba.util.oncokb.constants as oncokb_constants
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.util.sequenza import sequenza_reader 
from djerba.util.environment import directory_finder
from djerba.util.html import html_builder
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.oncokb.annotator import annotator_factory
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.oncokb.tools import gene_summary_reader
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.wgts.tools import wgts_tools

class cnv_processor(logger):

    ALTERATION_UPPER_CASE = 'ALTERATION'
    CENTROMERES = "hg38_centromeres.txt"
    HUGO_SYMBOL_UPPER_CASE = 'HUGO_SYMBOL'
    PLOT_FILENAME = 'seg_CNV_plot.svg'
    MINIMUM_MAGNITUDE_SEG_MEAN = 0.2
    GENOME_SIZE = 3095978931 # comes from https://www.ncbi.nlm.nih.gov/grc/human/data?asm=GRCh38.p12. Non-N bases. 
    SEG_FILENAME = 'seg.txt'

    def __init__(self, work_dir, config_wrapper, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir
        self.config = config_wrapper
        self.plot_path = os.path.join(self.work_dir, self.PLOT_FILENAME)
        self.seg_path = os.path.join(self.work_dir, self.SEG_FILENAME)
        self.data_dir = directory_finder(log_level, log_path).get_data_dir()        

    def calculate_percent_genome_altered(self):
        total = 0
        if not os.path.exists(self.seg_path):
            msg = "Cannot compute percent genome altered before "+\
                "generating SEG file: {0}".format(self.seg_path)
            self.logger.error(msg)
            raise RuntimeError(msg)
        with open(self.seg_path) as input_file:
            for row in csv.DictReader(input_file, delimiter="\t"):
                seg_mean = row['seg_mean']
                if seg_mean != 'NA' and abs(float(seg_mean)) >= self.MINIMUM_MAGNITUDE_SEG_MEAN:
                    total += int(row['loc_end']) - int(row['loc_start'])
        # TODO see GCGI-347 for possible updates to genome size
        fga = float(total)/self.GENOME_SIZE
        return int(round(fga*100, 0))

    def get_merge_inputs(self):
        """
        Read gene and therapy information for merge inputs
        Both are derived from the annotated CNA file
        """
        # read the tab-delimited input file
        gene_info = []
        gene_info_factory = gim_factory(self.log_level, self.log_path)
        summaries = gene_summary_reader(self.log_level, self.log_path)
        treatments = []
        treatment_option_factory = tom_factory(self.log_level, self.log_path)
        input_name = oncokb_constants.DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED
        oncotree_code = self.config.get_my_string(cnv.ONCOTREE_CODE)
        with open(os.path.join(self.work_dir, input_name)) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row_input in reader:
                # record the gene for all reportable alterations
                level = oncokb_levels.parse_oncokb_level(row_input)
                if level not in ['N3', 'N4', 'Unknown', 'NA']:
                    gene = row_input[self.HUGO_SYMBOL_UPPER_CASE]
                    gene_info_entry = gene_info_factory.get_json(
                        gene=gene,
                        summary=summaries.get(gene)
                    )
                    gene_info.append(gene_info_entry)
                # record therapy for all actionable alterations (OncoKB level 4 or higher)
                therapies = oncokb_levels.parse_actionable_therapies(row_input)
                for level in therapies.keys():
                    alt = row_input['ALTERATION']
                    alt_url = html_builder.build_alteration_url(gene, alt, oncotree_code)
                    treatment_entry = treatment_option_factory.get_json(
                        tier = oncokb_levels.tier(level),
                        level = level,
                        gene = gene,
                        alteration = alt,
                        alteration_url = alt_url,
                        treatments = therapies[level]
                    )
                    treatments.append(treatment_entry)
        # assemble the output
        merge_inputs = {
            'gene_information_merger': gene_info,
            'treatment_options_merger': treatments
        }
        return merge_inputs

    def get_results(self):
        """Read previous output into the JSON serializable results structure"""
        image_converter = converter(self.log_level, self.log_path)
        cnv_plot = image_converter.convert_svg(self.plot_path, 'CNV plot')
        rows = []
        wgts_toolkit = wgts_tools(self.log_level, self.log_path)
        is_wgts = wgts_toolkit.has_expression(self.work_dir)
        if is_wgts:
            self.logger.info("Reading expression from {0}".format(self.work_dir))
            mutation_expression = wgts_tools.read_expression(self.work_dir)
        else:
            self.logger.info("No expression data found")
            mutation_expression = {}
        cytobands = wgts_tools(self.log_level, self.log_path).cytoband_lookup()
        input_name = oncokb_constants.DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED
        with open(os.path.join(self.work_dir, input_name)) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row_input in reader:
                gene = row_input[self.HUGO_SYMBOL_UPPER_CASE]
                # if gene not found in cytoBands.txt, default to 'Unknown'
                row_output = {
                    cnv.EXPRESSION_PERCENTILE: mutation_expression.get(gene), # None for WGS
                    wgts_tools.GENE: gene,
                    cnv.GENE_URL: html_builder.build_gene_url(gene),
                    cnv.ALTERATION: row_input[self.ALTERATION_UPPER_CASE],
                    wgts_tools.CHROMOSOME: cytobands.get(gene, wgts_tools.UNKNOWN),
                    wgts_tools.ONCOKB: oncokb_levels.parse_oncokb_level(row_input)
                }
                rows.append(row_output)
        unfiltered_cnv_total = len(rows)
        self.logger.debug("Sorting and filtering CNV rows")
        rows = wgts_toolkit.sort_variant_rows(rows)
        rows = oncokb_levels.filter_reportable(rows)
        results = {
            cnv.PERCENT_GENOME_ALTERED: self.calculate_percent_genome_altered(),
            cnv.TOTAL_VARIANTS: unfiltered_cnv_total,
            cnv.CLINICALLY_RELEVANT_VARIANTS: len(rows),
            cnv.CNV_PLOT: cnv_plot,
            cnv.HAS_EXPRESSION_DATA: is_wgts,
            cnv.BODY: rows
        }
        return results

    def write_copy_states(self):
        """
        Write the copy states to JSON for later reference, eg. by snv/indel plugin
        """
        conversion = {
            0: "Neutral",
            1: "Gain",
            2: "Amplification",
            -1: "Shallow Deletion",
            -2: "Deep Deletion"
        }
        states = {}
        with open(os.path.join(self.work_dir, 'data_CNA.txt')) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            for row in reader:
                if row[0]!='Hugo_Symbol':
                    gene = row[0]
                    try:
                        cna = int(row[1])
                        states[gene] = conversion[cna]
                    except (TypeError, KeyError) as err:
                        msg = "Cannot convert unknown CNA code: {0}".format(row[1])
                        self.logger.error(msg)
                        raise RuntimeError(msg) from err
        with open(os.path.join(self.work_dir, cnv.COPY_STATE_FILE), 'w') as out_file:
            out_file.write(json.dumps(states, sort_keys=True, indent=4))

    def write_working_files(self):
        """
        Preprocess the SEG file
        Run the R scripts to write CNV results to the working directory
        Annotate results from OncoKB
        """
        # preprocess the input files
        gamma = self.config.get_my_int(cnv.SEQUENZA_GAMMA)
        sequenza_path = self.config.get_my_string(cnv.SEQUENZA_PATH)
        in_path = sequenza_reader(sequenza_path).extract_cn_seg_file(self.work_dir, gamma)
        with open(in_path, 'rt') as in_file, open(self.seg_path, 'wt') as out_file:
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            in_header = True
            for row in reader:
                if in_header:
                    in_header = False
                else:
                    row[0] = self.config.get_my_string(cnv.TUMOUR_ID)
                writer.writerow(row)
        # process data with main R script
        self.run_main_r_script()
        # write plot
        self.write_cnv_plot()
        # annotate
        factory = annotator_factory(self.log_level, self.log_path)
        factory.get_annotator(self.work_dir, self.config).annotate_cna()
        # write copy states
        self.write_copy_states()
