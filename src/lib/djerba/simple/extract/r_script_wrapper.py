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
    ONCOGENIC = 136

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

    def __init__(self, config, rscript_dir, out_dir, supplied_tmp_dir=None):
        self.config = config
        self.rscript_dir = os.path.realpath(rscript_dir)
        self.out_dir = out_dir
        self.supplied_tmp_dir = supplied_tmp_dir
        self.exclusions = [re.compile(x) for x in self.FILTER_FLAGS_EXCLUDE]
        self.oncokb_token = os.environ[self.ONCOKB_TOKEN_VARIABLE]

    def _annotate_cna(self, info_path):
        # TODO import the main() method of CnaAnnotator.py instead of running in subprocess
        # TODO as a stopgap, replace local paths with call to an executable script
        in_path = os.path.join(self.out_dir, self.DATA_CNA_ONCOKB_GENES_NON_DIPLOID)
        out_path = os.path.join(self.out_dir, self.DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED)
        cmd = [
            '/home/iain/oicr/workspace/venv/djerba/bin/python3',
            '/home/iain/oicr/git/oncokb-annotator/CnaAnnotator.py',
            '-i', in_path,
            '-o', out_path,
            '-c', info_path,
            '-b', self.oncokb_token
        ]
        print('###', ' '.join(cmd))
        result = subprocess.run(cmd, check=True)
        return out_path

    def _annotate_fusion(self, info_path):
        # TODO import the main() method of FusionAnnotator.py instead of running in subprocess
        # TODO as a stopgap, replace local paths with call to an executable script
        in_path = os.path.join(self.out_dir, self.DATA_FUSIONS_ONCOKB)
        out_path = os.path.join(self.out_dir, self.DATA_FUSIONS_ONCOKB_ANNOTATED)
        cmd = [
            '/home/iain/oicr/workspace/venv/djerba/bin/python3',
            '/home/iain/oicr/git/oncokb-annotator/FusionAnnotator.py',
            '-i', in_path,
            '-o', out_path,
            '-c', info_path,
            '-b', self.oncokb_token
        ]
        print('###', ' '.join(cmd))
        result = subprocess.run(cmd, check=True)
        return out_path

    def _annotate_maf(self, in_path, tmp_dir, info_path):
        # TODO import the main() method of MafAnnotator.py instead of running in subprocess
        # TODO as a stopgap, replace local paths with call to an executable script
        tmp_path = os.path.join(tmp_dir, "annotated_maf_tmp.tsv")
        cmd = [
            '/home/iain/oicr/workspace/venv/djerba/bin/python3',
            '/home/iain/oicr/git/oncokb-annotator/MafAnnotator.py',
            '-i', in_path,
            '-o', tmp_path,
            '-c', info_path,
            '-b', self.oncokb_token
        ]
        print('###', ' '.join(cmd))
        result = subprocess.run(cmd, check=True)
        # column header changed from lowercase to uppercase in newer versions of MafAnnotator
        # Rscript singleSample.r expects lowercase
        # TODO upgrade to newer version and leave header as-is?
        out_path = os.path.join(tmp_dir, self.ANNOTATED_MAF)
        with open(tmp_path) as tmp_file, open(out_path, 'w') as out_file:
            first = True
            reader = csv.reader(tmp_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            for row in reader:
                if first:
                    row[self.ONCOGENIC] = row[self.ONCOGENIC].lower()
                    first = False
                writer.writerow(row)
        return out_path

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

    def preprocess_gep(self, gep_path, tmp_dir):
        """
        Apply preprocessing to a GEP file; write results to tmp_dir
        CGI-Tools constructs the GEP file from scratch, but only the first column actually varies
        As a shortcut, we insert the first column into a ready-made file
        """
        # read the gene id and FPKM metric from the GEP file for this report
        fkpm = {}
        with open(gep_path) as gep_file:
            reader = csv.reader(gep_file, delimiter="\t")
            for row in reader:
                try:
                    fkpm[row[self.GENE_ID]] = row[self.FPKM]
                except IndexError:
                    print(row)
        # insert as the first column in the generic GEP file
        ref_path = self.config[constants.GEP_REFERENCE]
        out_path = os.path.join(tmp_dir, 'gep.txt')
        with \
             gzip.open(ref_path, 'rt', encoding=constants.TEXT_ENCODING) as in_file, \
             open(out_path, 'wt') as out_file:
            # preprocess the MAF file
            reader = csv.reader(in_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            first = True
            for row in reader:
                if first:
                    row.insert(1, self.config[constants.TUMOUR_ID])
                    first = False
                else:
                    gene_id = row[0]
                    try:
                        row.insert(1, fkpm[gene_id])
                    except KeyError as err:
                        msg = 'Cannot find gene ID {0} in '.format(gene_id) +\
                            'gep results path {0}'.format(gep_path)
                        raise KeyError(msg) from err
                writer.writerow(row)
        return out_path

    def preprocess_fus(self, fus_path, tmp_dir):
        """
        Apply preprocessing to a FUS file; write results to tmp_dir
        Prepend a column with the tumor id
        """
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
                    value = self.config[constants.TUMOUR_ID]
                new_row = [value] + row
                writer.writerow(new_row)
        return out_path

    def preprocess_maf(self, maf_path, tmp_dir, oncokb_info_path):
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
                        row[self.TUMOR_SAMPLE_BARCODE] = self.config[constants.TUMOUR_ID]
                        writer.writerow(row)
                        kept += 1
        print("Kept {0} of {1} MAF data rows".format(kept, total)) # TODO record with a logger
        # apply annotation to tempfile and return final output
        out_path = self._annotate_maf(tmp_path, tmp_dir, oncokb_info_path)
        return out_path

    def preprocess_seg(self, seg_path, tmp_dir):
        """
        Apply preprocessing to a SEG file; write results to tmp_dir
        Replace entry in the first column with the tumour ID
        """
        out_path = os.path.join(tmp_dir, 'seg.txt')
        with open(seg_path, 'rt') as seg_file, open(out_path, 'wt') as out_file:
            reader = csv.reader(seg_file, delimiter="\t")
            writer = csv.writer(out_file, delimiter="\t")
            in_header = True
            for row in reader:
                if in_header:
                    in_header = False
                else:
                    row[0] = self.config[constants.TUMOUR_ID]
                writer.writerow(row)
        return out_path

    def run(self):
        if self.supplied_tmp_dir == None:
            tmp = tempfile.TemporaryDirectory(prefix="djerba_r_script_")
            tmp_dir = tmp.name
        else:
            tmp_dir = self.supplied_tmp_dir
        oncokb_info = self.write_oncokb_info(tmp_dir)
        gep_path = self.preprocess_gep(self.config[constants.GEP_FILE], tmp_dir)
        fus_path = self.preprocess_fus(self.config[constants.FUS_FILE], tmp_dir)
        maf_path = self.preprocess_maf(self.config[constants.MAF_FILE], tmp_dir, oncokb_info)
        seg_path = self.preprocess_seg(self.config[constants.SEG_FILE], tmp_dir)
        cmd = [
            'Rscript', os.path.join(self.rscript_dir, 'singleSample.r'),
            '--basedir', self.rscript_dir,
            '--studyid', self.config[constants.STUDY_ID],
            '--tumourid', self.config[constants.TUMOUR_ID],
            '--normalid', self.config[constants.NORMAL_ID],
            '--maffile', maf_path,
            '--segfile', seg_path,
            '--gepfile', gep_path,
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
        result = subprocess.run(cmd, capture_output=True, encoding=constants.TEXT_ENCODING)
        self.postprocess(tmp_dir, oncokb_info)
        if self.supplied_tmp_dir == None:
            tmp.cleanup()
        return result

    def postprocess(self, tmp_dir, oncokb_info):
        """Apply postprocessing to the Rscript output directory"""
        self._annotate_cna(oncokb_info)
        self._annotate_fusion(oncokb_info)
        # remove unnecessary files, for consistency with CGI-Tools
        os.remove(os.path.join(self.out_dir, self.DATA_CNA_ONCOKB_GENES))
        os.remove(os.path.join(self.out_dir, self.DATA_FUSIONS_ONCOKB))

    def write_oncokb_info(self, info_dir):
        """Write a file of oncoKB data for use by annotation scripts"""
        info_path = os.path.join(info_dir, self.ONCOKB_CLINICAL_INFO)
        args = [self.config[constants.TUMOUR_ID], self.config[constants.CANCER_TYPE_DETAILED]]
        with open(info_path, 'w') as info_file:
            print("SAMPLE_ID\tONCOTREE_CODE", file=info_file)
            print("{0}\t{1}".format(*args), file=info_file)
        return info_path
