"""Functions of annotating MAF variants with oncoKB"""

import os
import logging

from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.logger import logger

class maf_annotater():

    ONCOKB_CLINICAL_INFO = 'oncokb_clinical_info.txt'

    # environment variable for ONCOKB token path
    ONCOKB_TOKEN_VARIABLE = 'ONCOKB_TOKEN'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = logger().get_logger(log_level, __name__, log_path)
        self.runner = subprocess_runner(log_level, log_path)

    def run_annotator_script(self, command, description):
        """Redact the OncoKB token (-b argument) from logging"""
        self.runner.run(command, description, ['-b',])

    def get_oncoKB_token(self):        
        with open(os.environ[self.ONCOKB_TOKEN_VARIABLE]) as token_file:
            oncokb_token = token_file.read().strip()
            return(oncokb_token)

    def write_oncokb_info(self, info_dir, tumour_id, oncotree_code):
        """Write a file of oncoKB data for use by annotation scripts"""
        info_path = os.path.join(info_dir, self.ONCOKB_CLINICAL_INFO)
        args = [tumour_id, oncotree_code]
        with open(info_path, 'w') as info_file:
            print("SAMPLE_ID\tONCOTREE_CODE", file=info_file)
            print("{0}\t{1}".format(*args), file=info_file)
        return info_path

    def annotate_maf(self, in_path, tmp_dir, info_path):
        # TODO import the main() method of MafAnnotator.py instead of running in subprocess
        out_path = os.path.join(tmp_dir, "annotated_maf_tmp.tsv")
        oncokb_token = self.get_oncoKB_token()
        cmd = [
            'MafAnnotator.py',
            '-i', in_path,
            '-o', out_path,
            '-c', info_path,
            '-b', oncokb_token
        ]
        self.run_annotator_script(cmd, 'MAF annotator')
        return out_path






