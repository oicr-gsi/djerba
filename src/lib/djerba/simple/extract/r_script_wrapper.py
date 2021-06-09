"""Wrapper to run the CGI-Tools legacy R script singleSample.r"""

import os
import subprocess
import djerba.simple.constants as constants

class wrapper:

    def __init__(self, config, rscript_dir, out_dir):
        self.config = config
        self.rscript_dir = os.path.realpath(rscript_dir)
        self.out_dir = out_dir

    def run(self):
        cmd = [
            'Rscript', os.path.join(self.rscript_dir, 'singleSample.r'),
            '--basedir', self.rscript_dir,
            '--studyid', self.config[constants.STUDY_ID],
            '--tumourid', self.config[constants.TUMOUR_ID],
            '--normalid', self.config[constants.NORMAL_ID],
            '--maffile', self.config[constants.MAF_FILE],
            '--segfile', self.config[constants.SEG_FILE],
            '--fusfile', self.config[constants.FUS_FILE],
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
        return result
