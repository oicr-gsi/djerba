"""Wrapper to run the CGI-Tools legacy R script singleSample.r"""

import csv
import gzip
import os
import re
import subprocess
import tempfile
import djerba.simple.constants as constants

class wrapper:

    # 0-based indices for important MAF columns
    VARIANT_CLASSIFICATION = 8
    TUMOR_SAMPLE_BARCODE = 15
    MATCHED_NORM_SAMPLE_BARCODE = 16
    T_DEPTH = 39
    T_ALT_COUNT = 41
    GNOMAD_AF = 123

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

    # maf filter thresholds
    MIN_VAF = 0.1
    MAX_UNMATCHED_GNOMAD_AF = 0.001

    def __init__(self, config, rscript_dir, out_dir, tmp_dir=None):
        self.config = config
        self.rscript_dir = os.path.realpath(rscript_dir)
        self.out_dir = out_dir
        self.tmp_dir = tmp_dir
        self.exclusions = [re.compile(x) for x in self.FILTER_FLAGS_EXCLUDE]

    def _maf_body_row_ok(self, row):
        """
        Should a MAF row be kept for output?
        Implements logic from functions.sh -> hard_filter_maf() in CGI-Tools
        Expected to filter out >99.9% of input reads
        """
        # TODO check only relevant column(s) against self.exclusions?
        ok = False
        row_t_depth = int(row[self.T_DEPTH])
        row_t_alt_count = float(row[self.T_ALT_COUNT]) if row[self.T_ALT_COUNT]!='' else 0.0
        row_gnomad_af = float(row[self.GNOMAD_AF]) if row[self.GNOMAD_AF]!='' else 0.0
        is_matched = row[self.MATCHED_NORM_SAMPLE_BARCODE] != 'unmatched'
        if row_t_depth >= 1 and \
           row_t_alt_count/row_t_depth >= self.MIN_VAF and \
           (is_matched or row_gnomad_af < self.MAX_UNMATCHED_GNOMAD_AF) and \
           row[self.VARIANT_CLASSIFICATION] in self.MUTATION_TYPES_EXONIC and \
           not any([any([x.search(z) for x in self.exclusions]) for z in row]):
            ok = True
        return ok

    def preprocess_fus(self, fus_path, tmp_dir):
        """Apply preprocessing to a FUS file; write results to tmp_dir"""
        return fus_path

    def preprocess_maf(self, maf_path, tmp_dir):
        """Apply preprocessing and annotation to a MAF file; write results to tmp_dir"""
        tmp_path = os.path.join(tmp_dir, 'tmp_maf.tsv')
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
                        in_header = False
                else:
                    total += 1
                    if self._maf_body_row_ok(row):
                        # filter rows in the MAF body and update the tumour_id
                        row[15] = self.config[constants.TUMOUR_ID]
                        writer.writerow(row)
                        kept += 1
        print("Kept {0} of {1} MAF data rows".format(kept, total))
        # apply annotation to tempfile and return final output
        out_path = tmp_path
        return out_path

    def preprocess_seg(self, seg_path, tmp_dir):
        """Apply preprocessing to a SEG file; write results to tmp_dir"""
        return seg_path

    def run(self):
        if self.tmp_dir == None:
            tmp = tempfile.TemporaryDirectory(prefix="djerba_r_script_")
            tmp_dir = tmp.name
        else:
            tmp_dir = self.tmp_dir
        fus_path = self.preprocess_fus(self.config[constants.FUS_FILE], tmp_dir)
        maf_path = self.preprocess_maf(self.config[constants.MAF_FILE], tmp_dir)
        seg_path = self.preprocess_seg(self.config[constants.SEG_FILE], tmp_dir)
        cmd = [
            'Rscript', os.path.join(self.rscript_dir, 'singleSample.r'),
            '--basedir', self.rscript_dir,
            '--studyid', self.config[constants.STUDY_ID],
            '--tumourid', self.config[constants.TUMOUR_ID],
            '--normalid', self.config[constants.NORMAL_ID],
            '--maffile', maf_path,
            '--segfile', seg_path,
            '--fusfile', fus_path,
            '--minfusionreads', self.config[constants.MIN_FUSION_READS],
            '--enscon', self.config[constants.ENSCON],
            '--entcon', self.config[constants.ENTCON],
            '--genebed', self.config[constants.GENE_BED],
            '--genelist', self.config[constants.GENE_LIST],
            '--oncolist', self.config[constants.ONCO_LIST],
            '--tcgadata', self.config[constants.TGCA_DATA],
            '--whizbam_url', self.config[constants.WHIZBAM_URL_KEY],
            '--tcgacode', self.config[constants.TGCA_CODE],
            '--gain', self.config[constants.GAIN],
            '--ampl', self.config[constants.AMPL],
            '--htzd', self.config[constants.HTZD],
            '--hmzd', self.config[constants.HMZD],
            '--outdir', self.out_dir
        ]
        print('###', ' '.join(cmd))
        result = subprocess.run(cmd, capture_output=True, encoding=constants.TEXT_ENCODING)
        if self.tmp_dir == None:
            tmp.cleanup()
        return result
