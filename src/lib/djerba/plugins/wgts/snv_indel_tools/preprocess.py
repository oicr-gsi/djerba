"""
The purpose of this file is deal with pre-processing necessary files for the SNV Indel plugin.
They're in a separate file because the pre-processing is a little more complex.
"""

# IMPORTS
import os
import re
import csv
import gzip
import logging
from djerba.util.logger import logger
from djerba.sequenza import sequenza_reader
from djerba.util.subprocess_runner import subprocess_runner
from djerba.extract.oncokb.annotator import oncokb_annotator
from shutil import copyfile
import djerba.plugins.wgts.snv_indel_tools.constants as constants 
from djerba.plugins.base import plugin_base
import pandas as pd
import djerba.plugins.wgts.snv_indel_tools.constants as sic
import djerba.render.constants as rc

class preprocess(logger):
 
    def __init__(self, report_dir, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.report_dir = report_dir
        self.tmp_dir = os.path.join(self.report_dir, 'tmp')
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

    def _maf_body_row_ok(self, row, ix, vaf_cutoff):
        """
        Should a MAF row be kept for output?
        Implements logic from functions.sh -> hard_filter_maf() in CGI-Tools
        Expected to filter out >99.9% of input reads
        ix is a dictionary of column indices
        """
        ok = False
        row_t_depth = int(row[ix.get(sic.T_DEPTH)])
        alt_count_raw = row[ix.get(sic.TUMOUR_ALT_COUNT)]
        gnomad_af_raw = row[ix.get(sic.GNOMAD_AF)]
        row_t_alt_count = float(alt_count_raw) if alt_count_raw!='' else 0.0
        row_gnomad_af = float(gnomad_af_raw) if gnomad_af_raw!='' else 0.0
        is_matched = row[ix.get(sic.MATCHED_NORM_SAMPLE_BARCODE)] != 'unmatched'
        filter_flags = re.split(';', row[ix.get(sic.FILTER)])
        if row_t_depth >= 1 and \
            row_t_alt_count/row_t_depth >= vaf_cutoff and \
            (is_matched or row_gnomad_af < self.MAX_UNMATCHED_GNOMAD_AF) and \
            row[ix.get(sic.VARIANT_CLASSIFICATION)] in sic.MUTATION_TYPES_EXONIC and \
            not any([z in sic.FILTER_FLAGS_EXCLUDE for z in filter_flags]):
            ok = True
        return ok

    def _read_maf_indices(self, row):
        indices = {}
        for i in range(len(row)):
            key = row[i]
            if key in sic.MAF_KEYS:
                indices[key] = i
        if set(indices.keys()) != set(sic.MAF_KEYS):
            msg = "Indices found in MAF header {0} ".format(indices.keys()) +\
                    "do not match required keys {0}".format(sic.MAF_KEYS)
            self.logger.error(msg)
            raise RuntimeError(msg)
        return indices

    def construct_whizbam_link( whizbam_base_url, studyid, tumourid, normalid, seqtype, genome):
        whizbam = "".join((whizbam_base_url,
                            "/igv?project1=", studyid,
                            "&library1=", tumourid,
                            "&file1=", tumourid, ".bam",
                            "&seqtype1=", seqtype,
                            "&project2=", studyid,
                            "&library2=", normalid,
                            "&file2=", normalid, ".bam",
                            "&seqtype2=", seqtype,
                            "&genome=", genome
                            ))
        return(whizbam)
  
    def preprocess_gep(self, gep_path):
        """
        Apply preprocessing to a GEP file; write results to tmp_dir
        CGI-Tools constructs the GEP file from scratch, but only one column actually varies
        As a shortcut, we insert the first column into a ready-made file
        TODO This is a legacy CGI-Tools method, is there a cleaner way to do it?
        TODO Should GEP_REFERENCE (list of past GEP results) be updated on a regular basis?
        """
        # read the gene id and FPKM metric from the GEP file for this report
        fkpm = {}
        with open(gep_path) as gep_file:
            reader = csv.reader(gep_file, delimiter="\t")
            for row in reader:
                try:
                    fkpm[row[sic.GEP_GENE_ID_INDEX]] = row[sic.GEP_FPKM_INDEX]
                except IndexError as err:
                    msg = "Incorrect number of columns in GEP row: '{0}'".format(row)+\
                        "read from '{0}'".format(gep_path)
                    self.logger.error(msg)
                    raise RuntimeError(msg) from err
        # insert as the second column in the generic GEP file
        ref_path = self.gep_reference
        out_path = os.path.join(self.tmp_dir, 'gep.txt')
        with \
            gzip.open(ref_path, 'rt', encoding=constants.TEXT_ENCODING) as in_file, \
            open(out_path, 'wt') as out_file:
            # preprocess the GEP file
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    row.insert(1, self.tumour_id)
                    first = False
                else:
                    gene_id = row[0]
                    try:
                        row.insert(1, fkpm[gene_id])
                    except KeyError as err:
                        msg = 'Reference gene ID {0} from {1} '.format(gene_id, ref_path) +\
                            'not found in gep results path {0}'.format(gep_path)
                        self.logger.warn(msg)
                        row.insert(1, '0.0')
                writer.writerow(row)
        return out_path
     
    def preprocess_maf(self, maf_path, assay, tumour_id):
        """Apply preprocessing and annotation to a MAF file; write results to tmp_dir"""
        tmp_path = os.path.join(self.tmp_dir, 'tmp_maf.tsv')
        if assay == "TAR":
            vaf_cutoff = sic.MIN_VAF_TAR
        else:
            vaf_cutoff = sic.MIN_VAF
        self.logger.info("Preprocessing MAF input")
        # find the relevant indices on-the-fly from MAF column headers
        # use this instead of csv.DictReader to preserve the rows for output
        with \
            gzip.open(maf_path, 'rt', encoding=constants.TEXT_ENCODING) as in_file, \
            open(tmp_path, 'wt') as tmp_file:
            # preprocess the MAF file
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(tmp_file, delimiter="\t")
            in_header = True
            total = 0
            kept = 0
            header_length = 0
            for row in reader:
                if in_header:
                    if re.match('#version', row[0]):
                        # do not write the version header
                        continue
                    else:
                        # write the column headers without change
                        writer.writerow(row)
                        indices = self._read_maf_indices(row)
                        header_length = len(row)
                        in_header = False
                else:
                    total += 1
                    if len(row) != header_length:
                        msg = "Indices found in MAF header are not of same length as rows!"
                        raise RuntimeError(msg)
                    if self._maf_body_row_ok(row, indices, vaf_cutoff):
                        # filter rows in the MAF body and update the tumour_id
                        row[indices.get(sic.TUMOUR_SAMPLE_BARCODE)] = tumour_id
                        writer.writerow(row)
                        kept += 1
        self.logger.info("Kept {0} of {1} MAF data rows".format(kept, total))
        # apply annotation to tempfile and return final output
        return tmp_path

    def run_R_code(self, whizbam_url, assay, raw_maf_file, tumour_id, oncotree_code):
        dir_location = os.path.dirname(__file__)
        tmp_maf_path = self.preprocess_maf(raw_maf_file, assay, tumour_id)
        annotated_maf_path = oncokb_annotator(
            tumour_id,
            oncotree_code,
            self.report_dir,
            self.tmp_dir,
            
            log_level=self.log_level,
            log_path=self.log_path
        ).annotate_maf(tmp_maf_path)

        #gep_path = self.preprocess_gep(self.gep_file)
        cmd = [
            'Rscript', os.path.join(dir_location + "/R/process_snv_data.r"),
                '--basedir', dir_location ,
                '--enscon', os.path.join(dir_location, '..', sic.ENSEMBL_CONVERSION), 
                '--tcgadata', sic.TCGA_RODIC,
                '--outdir', self.report_dir,
                '--whizbam_url', whizbam_url,
                '--maffile', annotated_maf_path

                ##expression
                #'--gepfile', gep_path,
                #'--tcgacode', self.tcgacode
                
        ]
        runner = subprocess_runner()
        result = runner.run(cmd, "main R script")
        return result
