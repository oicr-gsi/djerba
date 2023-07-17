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
import djerba.plugins.snv_indel.constants as constants 
from djerba.plugins.base import plugin_base
import pandas as pd

class preprocess():
 
  sequenza_path = "/.mounts/labs/CGI/cap-djerba/PASS01/PANX_1550/PANX_1550_Lv_M_WG_100-PM-064_LCM3_results.zip"
  gep_file = "/.mounts/labs/prod/vidarr/output-clinical/50b8/28fe/fb78/50b828fefb789e627fe6c47a9ee6a417de07c5e685cf7ea077a21e6e018c1869/PANX_1550_Lv_M_WT_100-PM-064_LCM3.genes.results"
  #maf_file = '/.mounts/labs/prod/vidarr/output-clinical/a4b0/7d4e/1634/a4b07d4e16340396340340a3fc0d3d31c509d997ccbaf384477775420d5ca2a2/PANX_1550_Lv_M_WG_100-PM-064_LCM3.filter.deduped.realigned.recalibrated.mutect2.filtered.maf.gz'
  maf_file = '/.mounts/labs/prod/vidarr/output-clinical/7ec2/a5da/1161/7ec2a5da1161cca72ace5c88a57f87c1782ed61b3109b2829b7bce082c054e9a/REVOLVE_0005_Pm_P_WG_REV-01-005_TUM.mutect2.filtered.maf.gz'
  tumour_id = "100-PM-064_LCM3"
  oncotree_code = "paad"
  tcgacode = "PAAD"
  
  gamma = 500
  solution = "_primary_"
  
  cache_params = None
  log_level = "logging.WARNING"
  log_path = "None"
  
  GENE_ID = 0
  FPKM = 6
  gep_reference = "/.mounts/labs/CGI/gsi/tools/djerba/gep_reference.txt.gz"
  
  # headers of important MAF columns
  VARIANT_CLASSIFICATION = 'Variant_Classification'
  TUMOUR_SAMPLE_BARCODE = 'Tumor_Sample_Barcode'
  MATCHED_NORM_SAMPLE_BARCODE = 'Matched_Norm_Sample_Barcode'
  FILTER = 'FILTER'
  T_DEPTH = 't_depth'
  T_ALT_COUNT = 't_alt_count'
  GNOMAD_AF = 'gnomAD_AF'
  MAF_KEYS = [
      VARIANT_CLASSIFICATION,
      TUMOUR_SAMPLE_BARCODE,
      MATCHED_NORM_SAMPLE_BARCODE,
      FILTER,
      T_DEPTH,
      T_ALT_COUNT,
      GNOMAD_AF
  ]


  # Permitted MAF mutation types
  # `Splice_Region` is *included* here, but *excluded* from the somatic mutation count used to compute TMB in report_to_json.py
  # See also JIRA ticket GCGI-469
  MUTATION_TYPES_EXONIC = [
      "3'Flank",
      "3'UTR",
      "5'Flank",
      "5'UTR",
      "Frame_Shift_Del",
      "Frame_Shift_Ins",
      "In_Frame_Del",
      "In_Frame_Ins",
      "Missense_Mutation",
      "Nonsense_Mutation",
      "Nonstop_Mutation",
      "Silent",
      "Splice_Region",
      "Splice_Site",
      "Targeted_Region",
      "Translation_Start_Site"
  ]

  # disallowed MAF filter flags; from filter_flags.exclude in CGI-Tools
  FILTER_FLAGS_EXCLUDE = [
      'str_contraction',
      't_lod_fstar'
  ]
  # MAF filter thresholds
  MIN_VAF = 0.1
  MIN_VAF_TAR = 0.01
  MAX_UNMATCHED_GNOMAD_AF = 0.001


  def __init__(self, config, work_dir, tar):
      self.config = config
      self.report_dir = work_dir
      self.tmp_dir = os.path.join(self.report_dir, 'tmp')
      if os.path.isdir(self.tmp_dir):
          print("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
          #self.logger.debug("Using tmp dir {0} for R script wrapper".format(self.tmp_dir))
      elif os.path.exists(self.tmp_dir):
          msg = "tmp dir path {0} exists but is not a directory".format(self.tmp_dir)
          #self.logger.error(msg)
          raise RuntimeError(msg)
      else:
          #print("Creating tmp dir {0} for R script wrapper".format(tmp_dir))
          #self.logger.debug("Creating tmp dir {0} for R script wrapper".format(self.tmp_dir))
          os.mkdir(self.tmp_dir)
      self.report_dir = work_dir
      #self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/plugins/tar/Rscripts/"
      self.tar = tar
      #if self.tar == True:
      #    self.seg_file = self.config['tar.swgs']['seg_file']
      #    self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/plugins/tar/Rscripts"
      #    self.r_script_dir_snv_indel = os.environ.get('DJERBA_BASE_DIR') + "/plugins/snv_indel/Rscripts"
      #else:
      #    self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/plugins/snv_indel/Rscripts/"
      #    self.r_script_dir_snv_indel = os.environ.get('DJERBA_BASE_DIR') + "/plugins/snv_indel/Rscripts/"
      self.r_script_dir = os.environ.get('DJERBA_BASE_DIR') + "/plugins/snv_indel/Rscripts/"
      #self.maf_file = maf_file


  # ----------------------- to do all the pre-processing --------------------
  
  def run_R_code(self):
  
    
    # FIX THIS BECAUSE THE ARATIO FILE IS DIFFERENT FOR TAR AND NONTAR
    if self.tar == True:
        maf_path = self.preprocess_maf(self.maf_file)
        #print(maf_path)
        #maf_path = "report/tmp/annotated_maf.tsv"
        #aratio_path = self.preprocess_seg_to_aratio(self.seg_file)
        #maf_path = "/tmp/annotated_maf.tsv"
        # do not process GEP, as that is for expression
        # need to process seg, as that is basically the aratio file and the copy number stuff. can just get this by running swgs plugin first 
        # don't know what maf does, need to look at it

        # MODIFY THIS MORE. I THINK ONLY THE MAF FILE WILL NEED PROCESSING BUT DOUBLE CHECK!!!!!!!!!!!
        cmd = [
         'Rscript', self.r_script_dir + "/process_CNA_data.r",
         '--basedir', self.r_script_dir,
         '--outdir', self.report_dir,
         '--whizbam_url', 'https://whizbam.oicr.on.ca',
         '--tumourid', self.tumour_id,
         '--normalid', '100-PM-064_BC',
         '--cbiostudy', 'PASS01',
         '--maffile', maf_path
        # '--aratiofile', aratio_path,
        # '--genebed', '/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/gencode_v33_hg38_genes.bed',
        # '--oncolist', os.environ.get('DJERBA_BASE_DIR') + "/data/20200818-oncoKBcancerGeneList.tsv",
        # '--genelist', '/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/targeted_genelist.txt'
        ]

   
    else:
        seg_path = self.preprocess_seg(self.sequenza_path)
        aratio_path = self.preprocess_aratio(self.sequenza_path, self.report_dir)
        gep_path = self.preprocess_gep(self.gep_file)
        maf_path = self.preprocess_maf(self.maf_file)
       
        cmd = [
            'Rscript', self.r_script_dir + "process_CNA_data.r",
            '--basedir', self.r_script_dir,
            '--outdir', self.report_dir,
            '--segfile', seg_path,
            '--genebed', "/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/gencode_v33_hg38_genes.bed",
            '--oncolist', os.environ.get('DJERBA_BASE_DIR') + "/data/20200818-oncoKBcancerGeneList.tsv",
            '--gain', "0.2529454648649786",
            '--ampl', "0.6927983480061226",
            '--htzd', "-0.3929375973235762",
            '--hmzd', "-1.7148656922109384",
            '--gepfile', gep_path,
            '--enscon', "/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/ensemble_conversion_hg38.txt", 
            '--genelist', "/.mounts/labs/gsi/modulator/sw/Ubuntu18.04/djerba-0.4.8/lib/python3.10/site-packages/djerba/data/targeted_genelist.txt",
            '--tcgadata', "/.mounts/labs/CGI/gsi/tools/RODiC/data",
            '--tcgacode', self.tcgacode,
            '--studyid', 'PASS01',
            '--whizbam_url', 'https://whizbam.oicr.on.ca',
            '--tumourid', self.tumour_id,
            '--normalid', '100-PM-064_BC',
            '--cbiostudy', 'PASS01',
            '--maffile', maf_path,
            '--aratiofile', aratio_path
        ]
    runner = subprocess_runner()
    result = runner.run(cmd, "main R script")
    self.postprocess()
    return result

  def preprocess_aratio(self, sequenza_path, report_dir):
    """
    Extract the appropriate _segments.txt file from the .zip archive output by Sequenza
    Copy the extracted file to report_dir
    """
    
    reader = sequenza_reader(sequenza_path)
    seg_path = reader.extract_segments_text_file(self.tmp_dir, self.gamma, self.solution)
    out_path = os.path.join(report_dir, 'aratio_segments.txt')
    copyfile(seg_path, out_path)
    return out_path
  
  #def preprocess_seg_to_aratio(self, seg_file):
  #  """
  #  We need to change some column names and entries in the .seg.txt file to make the dataframe suitable for plotting.
  #  Do this using pandas, then convert to a processed .seg.txt file.
  #  The reason for this wrangling is to force this file to look like aratio_segments.txt from the CNV plugin
  #  """
  #  #seg_path =  os.path.join(self.work_dir, seg_file)
  #  seg_path = seg_file
  #  # Create a dataframe
  #  df_seg = pd.read_csv(seg_path, sep = '\t')
  #
  #  # Change column names
  #  df_seg = df_seg.rename(columns = {"start":"start.pos", 
  #                                    "end":"end.pos", 
  #                                    "Corrected_Copy_Number":"CNt", 
  #                                    "chrom":"chromosome"})
  #
  #  # Add "chr" to the beginning of the chromosome numbers
  #  df_seg["chromosome"] = "chr" + df_seg["chromosome"].astype(str)
  #
  #  # Convert the dataframe back into a tab-delimited text file.
  #  out_path = os.path.join(self.report_dir, "seg_to_aratio.txt")
  #  df_seg.to_csv(out_path, sep = '\t', index=None)
  #  return out_path



  def preprocess_seg(self, sequenza_path):
    """
    Extract the SEG file from the .zip archive output by Sequenza
    Apply preprocessing and write results to tmp_dir
    Replace entry in the first column with the tumour ID
    """

    seg_path = sequenza_reader(sequenza_path).extract_cn_seg_file(self.tmp_dir, self.gamma)
    out_path = os.path.join(self.tmp_dir, 'seg.txt')
    with open(seg_path, 'rt') as seg_file, open(out_path, 'wt') as out_file:
        reader = csv.reader(seg_file, delimiter="\t")
        writer = csv.writer(out_file, delimiter="\t")
        in_header = True
        for row in reader:
            if in_header:
                in_header = False
            else:
                row[0] = self.tumour_id
            writer.writerow(row)
    return out_path
  
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
                fkpm[row[self.GENE_ID]] = row[self.FPKM]
            except IndexError as err:
                msg = "Incorrect number of columns in GEP row: '{0}'".format(row)+\
                      "read from '{0}'".format(gep_path)
                #self.logger.error(msg)
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
                    #self.logger.warn(msg)
                    row.insert(1, '0.0')
            writer.writerow(row)
    return out_path

  def preprocess_maf(self, maf_path):
    """Apply preprocessing and annotation to a MAF file; write results to tmp_dir"""
    tmp_path = os.path.join(self.tmp_dir, 'tmp_maf.tsv')
    #self.logger.info("Preprocessing MAF input")
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
        for row in reader:
            if in_header:
                if re.match('#version', row[0]):
                    # do not write the version header
                    continue
                else:
                    # write the column headers without change
                    writer.writerow(row)
                    indices = self._read_maf_indices(row)
                    in_header = False
            else:
                total += 1
                if self.tar:
                    if self._maf_body_row_ok(row, indices, self.MIN_VAF_TAR):
                        # filter rows in the MAF body and update the tumour_id
                        row[indices.get(self.TUMOUR_SAMPLE_BARCODE)] = self.tumour_id
                        writer.writerow(row)
                        kept += 1
                else:
                    if self._maf_body_row_ok(row, indices, self.MIN_VAF):
                        # filter rows in the MAF body and update the tumour_id
                        row[indices.get(self.TUMOUR_SAMPLE_BARCODE)] = self.tumour_id
                        writer.writerow(row)
                        kept += 1
    #self.logger.info("Kept {0} of {1} MAF data rows".format(kept, total))
    # apply annotation to tempfile and return final output
    out_path = oncokb_annotator(
        self.tumour_id,
        self.oncotree_code,
        self.report_dir,
        self.tmp_dir
        #self.cache_params,
        #self.log_level,
        #self.log_path
    ).annotate_maf(tmp_path)
    return out_path

  def _maf_body_row_ok(self, row, ix, vaf_cutoff):
    """
    Should a MAF row be kept for output?
    Implements logic from functions.sh -> hard_filter_maf() in CGI-Tools
    Expected to filter out >99.9% of input reads
    ix is a dictionary of column indices
    """
    ok = False
    row_t_depth = int(row[ix.get(self.T_DEPTH)])
    alt_count_raw = row[ix.get(self.T_ALT_COUNT)]
    gnomad_af_raw = row[ix.get(self.GNOMAD_AF)]
    row_t_alt_count = float(alt_count_raw) if alt_count_raw!='' else 0.0
    row_gnomad_af = float(gnomad_af_raw) if gnomad_af_raw!='' else 0.0
    is_matched = row[ix.get(self.MATCHED_NORM_SAMPLE_BARCODE)] != 'unmatched'
    filter_flags = re.split(';', row[ix.get(self.FILTER)])
    if row_t_depth >= 1 and \
        row_t_alt_count/row_t_depth >= vaf_cutoff and \
        (is_matched or row_gnomad_af < self.MAX_UNMATCHED_GNOMAD_AF) and \
        row[ix.get(self.VARIANT_CLASSIFICATION)] in self.MUTATION_TYPES_EXONIC and \
        not any([z in self.FILTER_FLAGS_EXCLUDE for z in filter_flags]):
        ok = True
    return ok

  def _read_maf_indices(self, row):
    indices = {}
    for i in range(len(row)):
        key = row[i]
        if key in self.MAF_KEYS:
            indices[key] = i
    if set(indices.keys()) != set(self.MAF_KEYS):
        msg = "Indices found in MAF header {0} ".format(indices.keys()) +\
                "do not match required keys {0}".format(self.MAF_KEYS)
        #self.logger.error(msg)
        raise RuntimeError(msg)
    return indices

  def postprocess(self):
     """
     Apply postprocessing to the Rscript output directory
     - Annotate CNA and (if any) fusion data
     - Remove unnecessary files written by the R script
     - Remove the temporary directory if required
     """
     annotator = oncokb_annotator(
            self.tumour_id,
            self.oncotree_code,
            self.report_dir,
            self.tmp_dir,
            self.cache_params,
     )
     annotator.annotate_cna()
        #if self.cleanup:
        #    rmtree(self.tmp_dir)
        #    os.remove(os.path.join(self.report_dir, constants.DATA_CNA_ONCOKB_GENES))
