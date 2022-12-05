"""Do OncoKB annotation by calling the scripts in oncokb-annotator"""

# The Python scripts in oncokb-annotator do not have a class structure and would be difficult to import
# Instead, we run them as subprocesses

import os
import logging
import djerba.util.constants as constants
from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.validator import path_validator

class oncokb_annotator(logger):

    # output filenames
    ANNOTATED_MAF = 'annotated_maf.tsv'
    DATA_CNA_ONCOKB_GENES_NON_DIPLOID = 'data_CNA_oncoKBgenes_nonDiploid.txt'
    DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED = 'data_CNA_oncoKBgenes_nonDiploid_annotated.txt'
    DATA_FUSIONS_ONCOKB = 'data_fusions_oncokb.txt'
    DATA_FUSIONS_ONCOKB_ANNOTATED = 'data_fusions_oncokb_annotated.txt'
    ONCOKB_CLINICAL_INFO = 'oncokb_clinical_info.txt'

    # environment variable for ONCOKB token path
    ONCOKB_TOKEN_VARIABLE = 'ONCOKB_TOKEN'

    # fields for empty oncoKB annotated fusion file
    ONCOKB_FUSION_ANNOTATED_HEADERS = [
        'Tumor_Sample_Barcode', 'Fusion', 'mutation_effect', 'ONCOGENIC',
        'LEVEL_1', 'LEVEL_2', 'LEVEL_3A', 'LEVEL_3B', 'LEVEL_4',
        'LEVEL_R1', 'LEVEL_R2', 'LEVEL_R3', 'HIGHEST_LEVEL', 'HIGHEST_SENSITIVE_LEVEL',
        'HIGHEST_RESISTANCE_LEVEL'
    ]

    def __init__(self, tumour_id, oncotree_code, report_dir, scratch_dir=None,
                 log_level=logging.WARNING, log_path=None):
        # report_dir is for input and (persistent) output; must contain appropriate input files
        # if given, scratch_dir is for working files not needed for final output
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)
        self.report_dir = report_dir
        self.validator.validate_output_dir(self.report_dir)
        if scratch_dir:
            self.scratch_dir = scratch_dir
            self.validator.validate_output_dir(self.scratch_dir)
        else:
            self.scratch_dir = self.report_dir
        self.runner = subprocess_runner(log_level, log_path)
        # Write sample name and oncotree code to a file, for use by annotation scripts
        self.info_path = os.path.join(self.scratch_dir, self.ONCOKB_CLINICAL_INFO)
        args = [tumour_id, oncotree_code]
        with open(self.info_path, 'w') as info_file:
            print("SAMPLE_ID\tONCOTREE_CODE", file=info_file)
            print("{0}\t{1}".format(*args), file=info_file)
        # Read the oncokb access token
        with open(os.environ[self.ONCOKB_TOKEN_VARIABLE]) as token_file:
            self.oncokb_token = token_file.read().strip()

    def _run_annotator_script(self, command, description):
        """Redact the OncoKB token (-b argument) from logging"""
        self.runner.run(command, description, ['-b',])
        
    def annotate_cna(self):
        in_path = os.path.join(self.report_dir, self.DATA_CNA_ONCOKB_GENES_NON_DIPLOID)
        self.validator.validate_input_file(in_path)
        out_path = os.path.join(self.report_dir, self.DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED)
        cmd = [
            'CnaAnnotator.py',
            '-i', in_path,
            '-o', out_path,
            '-c', self.info_path,
            '-b', self.oncokb_token
        ]
        self._run_annotator_script(cmd, 'CNA annotator')
        return out_path

    def annotate_fusion(self):
        in_path = os.path.join(self.report_dir, constants.DATA_FUSIONS_ONCOKB)
        self.validator.validate_input_file(in_path)
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
                '-c', self.info_path,
                '-b', self.oncokb_token
            ]
            self._run_annotator_script(cmd, 'fusion annotator')
        return out_path

    def annotate_maf(self, in_path):
        # unlike the CNA and Fusion methods, MAF annotation takes an input path argument
        self.validator.validate_input_file(in_path)
        out_path = os.path.join(self.scratch_dir, self.ANNOTATED_MAF)
        cmd = [
            'MafAnnotator.py',
            '-i', in_path,
            '-o', out_path,
            '-c', self.info_path,
            '-q', 'Genomic_Change',
            '-b', self.oncokb_token
        ]
        self._run_annotator_script(cmd, 'MAF annotator')
        return out_path
