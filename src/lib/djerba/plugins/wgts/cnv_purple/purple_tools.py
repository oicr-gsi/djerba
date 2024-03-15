"""
The purpose of this file is deal with pre-processing necessary files for the PURPLE plugin.
AUTHOR: Felix Beaudry
"""

import csv
import json
import logging
import os
import re
import tempfile
import zipfile

import djerba.plugins.wgts.cnv_purple.constants as cc
from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner


class process_purple(logger):

    COPY_STATE_FILE = 'purple_copy_states.json'

    def __init__(self, work_dir, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.work_dir = work_dir

    def analyze_segments(self, cnvfile, segfile, whizbam_url, purity, ploidy):
        dir_location = os.path.dirname(__file__)
        centromeres_file = os.path.join(dir_location, '../../..', cc.CENTROMERES)
        genebedpath = os.path.join(dir_location, '../../..', cc.GENEBED)
        cmd = [
            'Rscript', os.path.join(dir_location + "/r/process_segment_data.r"),
            '--outdir', self.work_dir,
            '--cnvfile', cnvfile,
            '--segfile', segfile,
            '--centromeres', centromeres_file,
            '--purity', str(purity),
            '--ploidy', str(ploidy),
            '--whizbam_url', whizbam_url,
            '--genefile', genebedpath
        ]
        runner = subprocess_runner()
        result = runner.run(cmd, "segments R script")
        return result.stdout.split('"')[1]

    def consider_purity_fit(self, purple_range_file):
        dir_location = os.path.dirname(__file__)
        cmd = [
            'Rscript', os.path.join(dir_location + "/r/process_fit.r"),
            '--range_file', purple_range_file,
            '--outdir', self.work_dir
        ]
        runner = subprocess_runner()
        result = runner.run(cmd, "fit R script")
        return result

    def convert_purple_to_gistic(self, purple_gene_file, ploidy):
        dir_location = os.path.dirname(__file__)
        oncolistpath = os.path.join(dir_location, '../../..', cc.ONCOLIST)
        cmd = [
            'Rscript', os.path.join(dir_location + "/r/process_CNA_data.r"),
            '--genefile', purple_gene_file,
            '--outdir', self.work_dir,
            '--oncolist', oncolistpath,
            '--ploidy', str(ploidy)
        ]
        runner = subprocess_runner()
        result = runner.run(cmd, "CNA R script")
        return result

    def unzip_purple(self, purple_zip):
        zf = zipfile.ZipFile(purple_zip)
        name_list = [x for x in zf.namelist() if not re.search('/$', x)]
        purple_files = {}
        for name in name_list:
            if re.search('purple\.purity\.range\.tsv$', name):
                purple_files[cc.PURPLE_PURITY_RANGE] = zf.extract(name, self.work_dir)
            elif re.search('purple\.cnv\.somatic\.tsv$', name):
                purple_files[cc.PURPLE_CNV] = zf.extract(name, self.work_dir)
            elif re.search('purple\.segment\.tsv$', name):
                purple_files[cc.PURPLE_SEG] = zf.extract(name, self.work_dir)
            elif re.search('purple\.cnv\.gene\.tsv$', name):
                purple_files[cc.PURPLE_GENE] = zf.extract(name, self.work_dir)
        return purple_files

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
        with open(os.path.join(self.work_dir, 'purple.data_CNA.txt')) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            for row in reader:
                if row[0] != 'Hugo_Symbol':
                    gene = row[0]
                    try:
                        cna = int(row[1])
                        states[gene] = conversion[cna]
                    except (TypeError, KeyError) as err:
                        msg = "Cannot convert unknown CNA code: {0}".format(row[1])
                        self.logger.error(msg)
                        raise RuntimeError(msg) from err
        with open(os.path.join(self.work_dir, self.COPY_STATE_FILE), 'w') as out_file:
            out_file.write(json.dumps(states, sort_keys=True, indent=4))

    def write_purple_alternate_launcher(self, path_info):
        bam_files = path_info.get(cc.BMPP)
        if not path_info.get(cc.MUTECT2) == None:
            vcf_index = ".".join((path_info.get(cc.MUTECT2), "tbi"))
        else:
            vcf_index = None
        purple_paths = {
            "purple.normal_bam": bam_files["whole genome normal bam"],
            "purple.normal_bai": bam_files["whole genome normal bam index"],
            "purple.tumour_bam": bam_files["whole genome tumour bam"],
            "purple.tumour_bai": bam_files["whole genome tumour bam index"],
            "purple.filterSV.vcf": path_info.get(cc.GRIDSS),
            "purple.filterSMALL.vcf": path_info.get(cc.MUTECT2),
            "purple.filterSMALL.vcf_index": vcf_index,
            "purple.runPURPLE.min_ploidy": 0,
            "purple.runPURPLE.max_ploidy": 8,
            "purple.runPURPLE.min_purity": 0,
            "purple.runPURPLE.max_purity": 1
        }
        return purple_paths


def construct_whizbam_link(studyid, tumourid):
    genome = cc.WHIZBAM_GENOME_VERSION
    whizbam_base_url = cc.WHIZBAM_BASE_URL
    seqtype = cc.WHIZBAM_SEQTYPE
    whizbam = "".join((whizbam_base_url,
                       "/igv?project1=", studyid,
                       "&library1=", tumourid,
                       "&file1=", tumourid, ".bam",
                       "&seqtype1=", seqtype,
                       "&genome=", genome
                       ))
    return whizbam


def fetch_purple_purity(purple_zip):
    tempdir = tempfile.TemporaryDirectory()
    tmp = tempdir.name
    zf = zipfile.ZipFile(purple_zip)
    name_list = [x for x in zf.namelist() if not re.search('/$', x)]
    for name in name_list:
        if re.search('purple\.purity\.range\.tsv$', name):
            purple_purity_path = zf.extract(name, tmp)
    with open(purple_purity_path, 'r') as purple_purity_file:
        purple_purity = csv.reader(purple_purity_file, delimiter="\t")
        header = True
        purity = []
        ploidy = []
        for row in purple_purity:
            if header:
                header = False
            else:
                try:
                    purity.append(row[0])
                    ploidy.append(row[4])
                except IndexError as err:
                    msg = "Incorrect number of columns in PURPLE Purity file: '{0}'".format(purple_purity_path)
                    raise RuntimeError(msg) from err
    purity_ploidy = {
        cc.PURITY: float(purity[0]),
        cc.PLOIDY: float(ploidy[0])
    }
    tempdir.cleanup()
    return purity_ploidy
