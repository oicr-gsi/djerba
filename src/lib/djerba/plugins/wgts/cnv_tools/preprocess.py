"""
The purpose of this file is deal with pre-processing necessary files for the SWGS plugin.
They're in a separate file because the pre-processing is a little more complex.
AUTHOR: Aqsa Alam
"""

# IMPORTS
import os
import csv
import gzip
import logging
import pandas as pd
from djerba.util.logger import logger
from djerba.sequenza import sequenza_reader
from djerba.util.subprocess_runner import subprocess_runner
from djerba.extract.oncokb.annotator import oncokb_annotator
from shutil import copyfile
import djerba.cnv_tools.constants as ctc 
import djerba.cnv_tools.constants as constants 
import djerba.snv_indel_tools.constants as sic
from djerba.snv_indel_tools.extract import data_builder as sit
import djerba.render.constants as rc
from djerba.util.image_to_base64 import converter
import djerba.extract.oncokb.constants as oncokb
from djerba.render.json_to_html import html_builder

class preprocess(logger):

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir
        self.tmp_dir = os.path.join(self.work_dir, 'tmp')
        if os.path.isdir(self.tmp_dir):
            print("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
            self.logger.debug("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
        elif os.path.exists(self.tmp_dir):
            msg = "tmp dir path {0} exists but is not a directory".format(self.tmp_dir)
            self.logger.error(msg)
            raise RuntimeError(msg)
        else:
            print("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
            self.logger.debug("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
            os.mkdir(self.tmp_dir)
  
    def build_copy_number_variation(self, assay, cna_annotated_path):
        cna_annotated_path = os.path.join(self.work_dir, cna_annotated_path)
        self.logger.debug("Building data for copy number variation table")
        rows = []
        if assay == "WGTS":
            mutation_expression = sit().read_expression()
        else:
            mutation_expression = {}
        with open(cna_annotated_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row in reader:
                gene = row[sic.HUGO_SYMBOL_UPPER_CASE]
                cytoband = sit().get_cytoband(gene)
                row = {
                    rc.EXPRESSION_METRIC: mutation_expression.get(gene), # None for WGS assay
                    rc.GENE: gene,
                    rc.GENE_URL: sit().build_gene_url(gene),
                    rc.ALT: row[sic.ALTERATION_UPPER_CASE],
                    rc.CHROMOSOME: cytoband,
                    'OncoKB level': sit().parse_oncokb_level(row)
                }
                rows.append(row)
        unfiltered_cnv_total = len(rows)
        self.logger.debug("Sorting and filtering CNV rows")
        rows = list(filter(sit().oncokb_filter, sit().sort_variant_rows(rows)))
        data_table = {
        #    sic.HAS_EXPRESSION_DATA: self.HAS_EXPRESSION_DATA,
            sic.TOTAL_VARIANTS: unfiltered_cnv_total,
            sic.CLINICALLY_RELEVANT_VARIANTS: len(rows),
            sic.BODY: rows
        }
        return data_table
    
    def calculate_percent_genome_altered(self, input_path):
        input_path = os.path.join(self.work_dir, input_path)
        total = 0
        with open(input_path) as input_file:
            for row in csv.DictReader(input_file, delimiter="\t"):
                if abs(float(row['seg.mean'])) >= ctc.MINIMUM_MAGNITUDE_SEG_MEAN:
                    total += int(row['loc.end']) - int(row['loc.start'])
        # TODO see GCGI-347 for possible updates to genome size
        fga = float(total)/ctc.GENOME_SIZE
        return int(round(fga*100, 0))

    def convert_to_gene_and_annotate(self, seg_path, purity, tumour_id, oncotree_code):
        dir_location = os.path.dirname(__file__)
        genebedpath = os.path.join(dir_location, '..', ctc.GENEBED)
        oncolistpath = os.path.join(dir_location, '..', sic.ONCOLIST)
        cmd = [
            'Rscript', os.path.join(dir_location + "/R/process_CNA_data.r"),
            '--basedir',dir_location,
            '--outdir', self.work_dir,
            '--segfile', seg_path,
            '--genebed', genebedpath,
            '--oncolist', oncolistpath,
            '--purity', purity
        ]

        runner = subprocess_runner()
        result = runner.run(cmd, "main R script")
        annotator = oncokb_annotator(
                        tumour_id,
                        oncotree_code,
                        self.work_dir,
                        self.tmp_dir
                        #self.cache_params
                )
        annotator.annotate_cna()

        return result

    def preprocess_seg_sequenza(self, sequenza_path, sequenza_gamma, tumour_id):
        """
        Extract the SEG file from the .zip archive output by Sequenza
        Apply preprocessing and write results to tmp_dir
        Replace entry in the first column with the tumour ID
        """
        seg_path = sequenza_reader(sequenza_path).extract_cn_seg_file(self.tmp_dir, sequenza_gamma)
        out_path = os.path.join(self.tmp_dir, 'seg.txt')
        with open(seg_path, 'rt') as seg_file, open(out_path, 'wt') as out_file:
            reader = csv.reader(seg_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            in_header = True
            for row in reader:
                if in_header:
                    in_header = False
                else:
                    row[0] = tumour_id
                writer.writerow(row)
        return out_path

    def preprocess_seg_tar(self, seg_file):
        """
        Filter for amplifications.
        """
        seg_path =  os.path.join(seg_file)
        # Create a dataframe so we can filter by amplifications only...or in this case, by gain only for testing.
        df_seg = pd.read_csv(seg_path, sep = '\t')
        df_seg = df_seg[df_seg["call"].str.contains("AMP|HLAMP") == True]

        # Delete the seg.mean column, and rename the Corrected_Copy_Number column to seg.mean
        df_seg = df_seg.drop(columns = "seg.median.logR")
        df_seg = df_seg.rename(columns={"Corrected_Copy_Number": "seg.mean"})
        df_seg = df_seg.rename(columns={"start": "loc.start"})
        df_seg = df_seg.rename(columns={"end": "loc.end"})

        # Convert the dataframe back into a tab-delimited text file.
        out_path = os.path.join(self.work_dir, 'seg_amplifications.txt')
        df_seg.to_csv(out_path, sep = '\t', index=None)

        return out_path
        
    def write_cnv_plot(self, sequenza_path, sequenza_gamma, sequenza_solution):
        segment_file = sequenza_reader(sequenza_path).extract_segments_text_file(self.work_dir, gamma=sequenza_gamma, solution=sequenza_solution)
        dir_location = os.path.dirname(__file__)
        out_path = os.path.join(self.work_dir, 'seg_CNV_plot.svg')
        args = [
            os.path.join(dir_location, 'R/cnv_plot.R'),
            '--segfile', segment_file ,
            '--segfiletype', 'sequenza',
            '-d',self.work_dir
        ]
        subprocess_runner(self.log_level, self.log_path).run(args)
        self.logger.info("Wrote CNV plot to {0}".format(out_path))
        base64_plot = converter().convert_svg(out_path, 'CNV plot')
        return base64_plot
    
    def build_therapy_info(self, variants_annotated_file, oncotree_uc):
        # build the "FDA approved" and "investigational" therapies data
        # defined respectively as OncoKB levels 1/2/R1 and R2/3A/3B/4
        # OncoKB "LEVEL" columns contain treatment if there is one, 'NA' otherwise
        # Input files:
        # - One file each for CNVs
        # - Must be annotated by OncoKB script
        # - Must not be missing
        # - May consist of headers only (no data rows)
        # Output columns:
        # - the gene name, with oncoKB link (or pair of names/links, for fusions)
        # - Alteration name, eg. HGVSp_Short value, with oncoKB link
        # - Treatment
        # - OncoKB level
        tiered_rows = list()
        for tier in (sic.FDA_APPROVED, sic.INVESTIGATIONAL):
            self.logger.debug("Building therapy info for level: {0}".format(tier))
            if tier == sic.FDA_APPROVED:
                levels = oncokb.FDA_APPROVED_LEVELS
            elif tier == sic.INVESTIGATIONAL:
                levels = oncokb.INVESTIGATIONAL_LEVELS
            rows = []
            with open(variants_annotated_file) as data_file:
                for row in csv.DictReader(data_file, delimiter="\t"):
                    gene = row[sic.HUGO_SYMBOL_UPPER_CASE]
                    alteration = row[sic.ALTERATION_UPPER_CASE]
                    [max_level, therapies] = sit().parse_max_oncokb_level_and_therapies(row, levels)
                    if max_level:
                        rows.append(self.treatment_row(gene, alteration, max_level, therapies, oncotree_uc, tier))
            rows = list(filter(sit().oncokb_filter, sit().sort_therapy_rows(rows)))
            if rows:
                tiered_rows.append(rows)
        return tiered_rows

