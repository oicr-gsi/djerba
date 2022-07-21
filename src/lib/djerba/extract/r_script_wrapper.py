"""Wrapper to run the CGI-Tools legacy R script singleSample.r"""

import csv
import gzip
import logging
import os
import re
import tempfile
import zipfile
import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.sequenza import sequenza_reader
from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner

class r_script_wrapper(logger):

    # headers of important MAF columns
    VARIANT_CLASSIFICATION = 'Variant_Classification'
    TUMOUR_SAMPLE_BARCODE = 'Tumor_Sample_Barcode'
    MATCHED_NORM_SAMPLE_BARCODE = 'Matched_Norm_Sample_Barcode'
    T_DEPTH = 't_depth'
    T_ALT_COUNT = 't_alt_count'
    GNOMAD_AF = 'gnomAD_AF'
    MAF_KEYS = [
        VARIANT_CLASSIFICATION,
        TUMOUR_SAMPLE_BARCODE,
        MATCHED_NORM_SAMPLE_BARCODE,
        T_DEPTH,
        T_ALT_COUNT,
        GNOMAD_AF
    ]

    # 0-based index for GEP results file
    GENE_ID = 0
    FPKM = 6

    # permitted MAF mutation types; from mutation_types.exonic in CGI-Tools
    MUTATION_TYPES_EXONIC = [
        'Frame_Shift_Del',
        'Frame_Shift_Ins',
        'In_Frame_Del',
        'In_Frame_Ins',
        'Missense_Mutation',
        'Nonsense_Mutation',
        'Nonstop_Mutation',
        'Silent',
        'Splice_Site',
        'Translation_Start_Site'
    ]

    # disallowed MAF filter flags; from filter_flags.exclude in CGI-Tools
    FILTER_FLAGS_EXCLUDE = [
        'str_contraction',
        't_lod_fstar'
    ]

    # MAF filter thresholds
    MIN_VAF = 0.1
    MAX_UNMATCHED_GNOMAD_AF = 0.001

    # output filenames
    ANNOTATED_MAF = 'annotated_maf.tsv'
    DATA_CNA_ONCOKB_GENES = 'data_CNA_oncoKBgenes.txt'
    DATA_CNA_ONCOKB_GENES_NON_DIPLOID = 'data_CNA_oncoKBgenes_nonDiploid.txt'
    DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED = 'data_CNA_oncoKBgenes_nonDiploid_annotated.txt'
    DATA_FUSIONS_ONCOKB = 'data_fusions_oncokb.txt'
    DATA_FUSIONS_ONCOKB_ANNOTATED = 'data_fusions_oncokb_annotated.txt'
    ONCOKB_CLINICAL_INFO = 'oncokb_clinical_info.txt'

    # environment variable for ONCOKB token path
    ONCOKB_TOKEN_VARIABLE = 'ONCOKB_TOKEN'

    # fields for empty oncoKB annotated fusion file
    ONCOKB_FUSION_ANNOTATED_HEADERS = [
        'Tumor_Sample_Barcode', 'Fusion', 'mutation_effect', 'oncogenic',
        'LEVEL_1', 'LEVEL_2', 'LEVEL_3A', 'LEVEL_3B', 'LEVEL_4',
        'LEVEL_R1', 'LEVEL_R2', 'LEVEL_R3', 'Highest_level'
    ]

    def __init__(self, config, report_dir, wgs_only, tmp_dir=None,
                 log_level=logging.WARNING, log_path=None):
        self.config = config
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.runner = subprocess_runner(log_level, log_path)
        self.r_script_dir = os.path.join(os.path.dirname(__file__), '..', 'R_stats')
        self.wgs_only = wgs_only
        self.supplied_tmp_dir = tmp_dir # may be None
        self.report_dir = report_dir
        self.tumour_id = config[ini.DISCOVERED][ini.TUMOUR_ID]
        self.oncotree_code = config[ini.INPUTS][ini.ONCOTREE_CODE]
        self.gep_reference = config[ini.SETTINGS][ini.GEP_REFERENCE]
        self.min_fusion_reads = self.config[ini.SETTINGS][ini.MIN_FUSION_READS]
        if not self.min_fusion_reads.isdigit():
            msg = "Min fusion reads '{}' is not a non-negative integer".format(min_fusion_reads)
            raise ValueError(msg)
        with open(os.environ[self.ONCOKB_TOKEN_VARIABLE]) as token_file:
            self.oncokb_token = token_file.read().strip()

    def _annotate_cna(self, info_path):
        # TODO import the main() method of CnaAnnotator.py instead of running in subprocess
        in_path = os.path.join(self.report_dir, self.DATA_CNA_ONCOKB_GENES_NON_DIPLOID)
        out_path = os.path.join(self.report_dir, self.DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED)
        cmd = [
            'CnaAnnotator.py',
            '-i', in_path,
            '-o', out_path,
            '-c', info_path,
            '-b', self.oncokb_token
        ]
        self._run_annotator_script(cmd, 'CNA annotator')
        return out_path

    def _annotate_fusion(self, info_path):
        # TODO import the main() method of FusionAnnotator.py instead of running in subprocess
        in_path = os.path.join(self.report_dir, self.DATA_FUSIONS_ONCOKB)
        out_path = os.path.join(self.report_dir, self.DATA_FUSIONS_ONCOKB_ANNOTATED)
        with open(in_path) as in_file:
            total = len(in_file.readlines())
        if total == 0:
            # should never happen, but include for completeness
            msg = "Fusion input {0} cannot be empty -- header is expected".format(in_path)
            self.logger.error(msg)
            raise RuntimeError(msg)
        elif total==1:
            # input has only a header -- write the oncoKB annotated header
            self.logger.info("Empty fusion input, writing empty oncoKB annotated file")
            with open(out_path, 'w') as out_file:
                out_file.write("\t".join(self.ONCOKB_FUSION_ANNOTATED_HEADERS)+"\n")
        else:
            msg = "Read {0} lines of fusion input, running Fusion annotator".format(total)
            self.logger.debug(msg)
            cmd = [
                'FusionAnnotator.py',
                '-i', in_path,
                '-o', out_path,
                '-c', info_path,
                '-b', self.oncokb_token
            ]
            self._run_annotator_script(cmd, 'fusion annotator')
        return out_path

    def _annotate_maf(self, in_path, tmp_dir, info_path):
        # TODO import the main() method of MafAnnotator.py instead of running in subprocess
        out_path = os.path.join(tmp_dir, "annotated_maf_tmp.tsv")
        cmd = [
            'MafAnnotator.py',
            '-i', in_path,
            '-o', out_path,
            '-c', info_path,
            '-b', self.oncokb_token
        ]
        self._run_annotator_script(cmd, 'MAF annotator')
        return out_path

    def _get_config_field(self, name):
        """
        Brute-force method to get a named field from config, without caring about section name
        Returns the first non-null match, None otherwise
        TODO Could replace with eg. a class to wrap the ConfigParser object
        """
        val = None
        sections = [
            ini.INPUTS,
            ini.SETTINGS,
            ini.DISCOVERED,
            ini.SAMPLE_META
        ]
        for section in sections:
            val = self.config[section].get(name)
            if val != None:
                break
        return val

    def _maf_body_row_ok(self, row, ix):
        """
        Should a MAF row be kept for output?
        Implements logic from functions.sh -> hard_filter_maf() in CGI-Tools
        Expected to filter out >99.9% of input reads
        ix is a dictionary of column indices
        """
        # TODO check only relevant column(s) against FILTER_FLAGS_EXCLUDE?
        ok = False
        row_t_depth = int(row[ix.get(self.T_DEPTH)])
        alt_count_raw = row[ix.get(self.T_ALT_COUNT)]
        gnomad_af_raw = row[ix.get(self.GNOMAD_AF)]
        row_t_alt_count = float(alt_count_raw) if alt_count_raw!='' else 0.0
        row_gnomad_af = float(gnomad_af_raw) if gnomad_af_raw!='' else 0.0
        is_matched = row[ix.get(self.MATCHED_NORM_SAMPLE_BARCODE)] != 'unmatched'
        if row_t_depth >= 1 and \
           row_t_alt_count/row_t_depth >= self.MIN_VAF and \
           (is_matched or row_gnomad_af < self.MAX_UNMATCHED_GNOMAD_AF) and \
           row[ix.get(self.VARIANT_CLASSIFICATION)] in self.MUTATION_TYPES_EXONIC and \
           not any([z in self.FILTER_FLAGS_EXCLUDE for z in row]):
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
            self.logger.error(msg)
            raise RuntimeError(msg)
        return indices

    def _run_annotator_script(self, command, description):
        """Redact the OncoKB token (-b argument) from logging"""
        self.runner.run(command, description, ['-b',])

    def _write_clinical_data(self):
        headers = [
            ini.PATIENT, # was PATIENT_LIMS_ID in CGI-Tools, eg. PANX_1249
            ini.PATIENT_ID, # was PATIENT_STUDY_ID, eg. 100-PM-013
            ini.TUMOUR_ID, # was TUMOUR_SAMPLE_ID
            ini.NORMAL_ID, # was BLOOD_SAMPLE_ID
            ini.REPORT_VERSION,
            ini.SAMPLE_TYPE,
            ini.CANCER_TYPE,
            ini.CANCER_TYPE_DETAILED,
            ini.CANCER_TYPE_DESCRIPTION,
            ini.DATE_SAMPLE_RECIEVED,
            ini.CLOSEST_TCGA,
            ini.SAMPLE_ANATOMICAL_SITE,
            ini.SAMPLE_PRIMARY_OR_METASTASIS,
            ini.MEAN_COVERAGE,
            ini.PCT_V7_ABOVE_80X,
            ini.SEQUENZA_PURITY_FRACTION,
            ini.SEQUENZA_PLOIDY,
            ini.QC_STATUS,
            ini.QC_COMMENT,
            ini.SEX
        ]
        body = []
        for header in headers:
            key = getattr(ini, header)
            val = self._get_config_field(key)
            if val == None:
                val = 'NA'
            body.append(str(val))
        out_path = os.path.join(self.report_dir, 'data_clinical.txt')
        with open(out_path, 'w') as out_file:
            print("\t".join(headers), out_file)
            print("\t".join(body), out_file)

    def preprocess_gep(self, gep_path, tmp_dir):
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
                    self.logger.error(msg)
                    raise RuntimeError(msg) from err
        # insert as the second column in the generic GEP file
        ref_path = self.gep_reference
        out_path = os.path.join(tmp_dir, 'gep.txt')
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

    def preprocess_fus(self, mavis_path, tmp_dir):
        """
        Extract the FUS file from the .zip archive output by Mavis
        Apply preprocessing and write results to tmp_dir
        Prepend a column with the tumour id
        """
        zf = zipfile.ZipFile(mavis_path)
        matched = []
        for name in zf.namelist():
            if re.search('mavis_summary_all_.*\.tab$', name):
                matched.append(name)
        if len(matched) == 0:
            msg = "Could not find Mavis summary .tab in "+mavis_path
            raise RuntimeError(msg)
        elif len(matched) > 1:
            msg = "Found more than one Mavis summary .tab file in "+mavis_path
            raise RuntimeError(msg)
        fus_path = zf.extract(matched[0], tmp_dir)
        # prepend column to the extracted summary path
        out_path = os.path.join(tmp_dir, 'fus.txt')
        with open(fus_path, 'rt') as fus_file, open(out_path, 'wt') as out_file:
            reader = csv.reader(fus_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            in_header = True
            for row in reader:
                if in_header:
                    value = 'Sample'
                    in_header = False
                else:
                    value = self.tumour_id
                new_row = [value] + row
                writer.writerow(new_row)
        return out_path

    def preprocess_maf(self, maf_path, tmp_dir, oncokb_info_path):
        """Apply preprocessing and annotation to a MAF file; write results to tmp_dir"""
        tmp_path = os.path.join(tmp_dir, 'tmp_maf.tsv')
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
                    if self._maf_body_row_ok(row, indices):
                        # filter rows in the MAF body and update the tumour_id
                        row[indices.get(self.TUMOUR_SAMPLE_BARCODE)] = self.tumour_id
                        writer.writerow(row)
                        kept += 1
        self.logger.info("Kept {0} of {1} MAF data rows".format(kept, total))
        # apply annotation to tempfile and return final output
        out_path = self._annotate_maf(tmp_path, tmp_dir, oncokb_info_path)
        return out_path

    def preprocess_seg(self, sequenza_path, tmp_dir):
        """
        Extract the SEG file from the .zip archive output by Sequenza
        Apply preprocessing and write results to tmp_dir
        Replace entry in the first column with the tumour ID
        """
        gamma = self.config.getint(ini.DISCOVERED, ini.SEQUENZA_GAMMA)
        seg_path = sequenza_reader(sequenza_path).extract_seg_file(tmp_dir, gamma)
        out_path = os.path.join(tmp_dir, 'seg.txt')
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

    def preprocess_msi(self, msi_path, report_dir):
        """
        Copy and reconfigure msisensor output file
        Remove empty trailing lines
        Rename header/first line
        To-do: Add bootstrap analysis
        """
        out_path = os.path.join(report_dir, 'msi.txt')
        with open(msi_path, 'rt') as msi_file, open(out_path, 'wt') as out_file:
            reader = csv.reader(msi_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            in_header = True
            for row in reader:
                if in_header:
                    in_header = False
                    row[2] = "MSI"
                    writer.writerow(row)
                elif row:
                    writer.writerow(row)
        return out_path


    def run(self):
        if self.supplied_tmp_dir == None:
            tmp = tempfile.TemporaryDirectory(prefix="djerba_r_script_")
            tmp_dir = tmp.name
        else:
            tmp_dir = self.supplied_tmp_dir
        oncokb_info = self.write_oncokb_info(tmp_dir)
        self.preprocess_msi(self.config[ini.DISCOVERED][ini.MSI_FILE], self.report_dir)
        maf_path = self.preprocess_maf(self.config[ini.DISCOVERED][ini.MAF_FILE], tmp_dir, oncokb_info)
        seg_path = self.preprocess_seg(self.config[ini.DISCOVERED][ini.SEQUENZA_FILE], tmp_dir)
        cmd = [
            'Rscript', os.path.join(self.r_script_dir, 'singleSample.r'),
            '--basedir', self.r_script_dir,
            '--studyid', self.config[ini.INPUTS][ini.STUDY_ID],
            '--tumourid', self.tumour_id,
            '--normalid', self.config[ini.DISCOVERED][ini.NORMAL_ID],
            '--maffile', maf_path,
            '--segfile', seg_path,
            '--minfusionreads', self.min_fusion_reads,
            '--enscon', self.config[ini.DISCOVERED][ini.ENSCON],
            '--entcon', self.config[ini.DISCOVERED][ini.ENTCON],
            '--genebed', self.config[ini.DISCOVERED][ini.GENE_BED],
            '--genelist', self.config[ini.DISCOVERED][ini.GENE_LIST],
            '--oncolist', self.config[ini.DISCOVERED][ini.ONCO_LIST],
            '--tcgadata', self.config[ini.SETTINGS][ini.TCGA_DATA],
            '--whizbam_url', self.config[ini.SETTINGS][ini.WHIZBAM_URL],
            '--tcgacode', self.config[ini.INPUTS][ini.TCGA_CODE].upper(),
            '--gain', self.config[ini.DISCOVERED][ini.LOG_R_GAIN],
            '--ampl', self.config[ini.DISCOVERED][ini.LOG_R_AMPL],
            '--htzd', self.config[ini.DISCOVERED][ini.LOG_R_HTZD],
            '--hmzd', self.config[ini.DISCOVERED][ini.LOG_R_HMZD],
            '--outdir', self.report_dir
        ]
        if not self.wgs_only:
            gep_path = self.preprocess_gep(self.config[ini.DISCOVERED][ini.GEP_FILE], tmp_dir)
            fus_path = self.preprocess_fus(self.config[ini.DISCOVERED][ini.MAVIS_FILE], tmp_dir)
            cmd.extend([
                '--gepfile', gep_path,
                '--fusfile', fus_path,
            ])
        result = self.runner.run(cmd, "main R script")
        self.postprocess(oncokb_info)
        if self.supplied_tmp_dir == None:
            tmp.cleanup()
        return result


    def postprocess(self, oncokb_info):
        """
        Apply postprocessing to the Rscript output directory:
        - Annotate CNA and (if any) fusion data
        - Remove unnecessary files, for consistency with CGI-Tools
        """
        self._annotate_cna(oncokb_info)
        os.remove(os.path.join(self.report_dir, self.DATA_CNA_ONCOKB_GENES))
        if not self.wgs_only:
            self._annotate_fusion(oncokb_info)
            os.remove(os.path.join(self.report_dir, self.DATA_FUSIONS_ONCOKB))

    def write_oncokb_info(self, info_dir):
        """Write a file of oncoKB data for use by annotation scripts"""
        info_path = os.path.join(info_dir, self.ONCOKB_CLINICAL_INFO)
        args = [self.tumour_id, self.oncotree_code]
        with open(info_path, 'w') as info_file:
            print("SAMPLE_ID\tONCOTREE_CODE", file=info_file)
            print("{0}\t{1}".format(*args), file=info_file)
        return info_path
