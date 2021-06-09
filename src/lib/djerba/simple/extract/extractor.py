"""Extract and pre-process data, so it can be read into a clinical report JSON document"""

import json
import os
import pandas as pd
import subprocess

from djerba.simple.extract.sequenza import sequenza_extractor
import djerba.simple.constants as constants


class extractor:
    """
    Extract the clinical report data; replaces 4-singleSample.sh
    Input: config from 'discover' step; replaces INI config from 3-configureSingleSample.sh
    Output: Directory of .txt and .json files for downstream processing
    """

    SAMPLE_INFO_KEY = 'sample_info'
    SAMPLE_PARAMS_FILENAME = 'sample_params.json'
    MAF_PARAMS_FILENAME = 'maf_params.json'
    SEQUENZA_PARAMS_FILENAME = 'sequenza_params.json'
    
    def __init__(self, config, bedPath, outDir, rscript_dir):
        # config is a dictionary with required parameters (eg. from INI file)
        self.config = config
        self.bedPath = bedPath # .bed file for MAF calculation; TODO check readability?
        self.outDir = outDir
        self.rscript_dir = rscript_dir
        self.componentPaths = []

    def _write_json(self, config, fileName):
        outPath = os.path.join(self.outDir, fileName)
        with open(outPath, 'w') as out:
            out.write(json.dumps(config, sort_keys=True, indent=4))
        return outPath

    def getComponentPaths(self):
        """JSON component paths to create reader objects and build the report"""
        return self.componentPaths

    def run(self):
        """Run all extractions and write output"""
        self.componentPaths.append(self.writeMafParams())
        self.componentPaths.append(self.writeSequenzaParams())
        self.componentPaths.append(self.writeConfigParams())

    def run_Rscript(self):
        """Run the singleSample.r legacy script"""
        cmd = [
            'Rscript', os.path.join(self.rscript_dir, 'singleSample.r'),
            '--basedir', self.rscript_dir,
            '--studyid', self.config[constants.STUDY_ID],
            '--tumourid', self.config[constants.TUMOR_ID],
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
            '--outdir', self.config[constants.OUT_DIR]
        ]
        result = subprocess.run(cmd, capture_output=True)

    def writeConfigParams(self):
        """
        Take parameters directly from extraction config, and write as JSON for later use
        Output approximates data_clinical.txt in CGI-Tools, but only has fields for final JSON output
        """
        sampleParams = {}
        sampleParams['PATIENT_ID'] = self.config[constants.PATIENT_ID].strip('"')
        stringKeys = [
            'SAMPLE_TYPE',
            'CANCER_TYPE',
            'CANCER_TYPE_DETAILED',
            'CANCER_TYPE_DESCRIPTION',
            'DATE_SAMPLE_RECEIVED',
            'CLOSEST_TCGA',
            'SAMPLE_ANATOMICAL_SITE',
            'SAMPLE_PRIMARY_OR_METASTASIS',
            'SEX'
        ]
        floatKeys = [
            'MEAN_COVERAGE',
            'PCT_v7_ABOVE_80x',
            'SEQUENZA_PURITY_FRACTION',
            'SEQUENZA_PLOIDY'
        ]
        # TODO if value is empty, should we replace with NA? Or raise an error?
        # TODO can other values be used? Is 'patient'=='SAMPLE_ID'?
        for key in stringKeys:
            # annoyingly, ConfigParser converts keys to lowercase
            # see https://stackoverflow.com/questions/19359556/configparser-reads-capital-keys-and-make-them-lower-case
            # TODO find a less hacky solution to this issue
            configKey = key.lower()
            if configKey in self.config:
                # TODO print a warning for missing key?
                sampleParams[key] = self.config[configKey].strip('"')
        for key in floatKeys:
            configKey = key.lower()
            if configKey in self.config:
                sampleParams[key] = float(self.config[configKey])
        config = {
            constants.READER_CLASS_KEY: 'json_reader',
            self.SAMPLE_INFO_KEY: sampleParams
        }
        return self._write_json(config, self.SAMPLE_PARAMS_FILENAME)

    def writeMafParams(self):
        """Read the MAF file, extract relevant parameters, and write as JSON"""
        maf_path = self.config[constants.MAF_FILE]
        tmb = maf_extractor(maf_path, self.bedPath).find_tmb()
        config = {
            constants.READER_CLASS_KEY: 'json_reader',
            self.SAMPLE_INFO_KEY: {
                constants.TMB_PER_MB_KEY: tmb
            }
        }
        return self._write_json(config, self.MAF_PARAMS_FILENAME)

    def writeSequenzaParams(self):
        """Read the Sequenza results.zip, extract relevant parameters, and write as JSON"""
        ex = sequenza_extractor(self.config[constants.SEQUENZAFILE])
        gamma = self.config.get(constants.SEQUENZA_GAMMA)
        [purity, ploidy] = ex.get_purity_ploidy(gamma) # if gamma==None, this uses the default
        config = {
            constants.READER_CLASS_KEY: 'json_reader',
            self.SAMPLE_INFO_KEY: {
                constants.SEQUENZA_PURITY_KEY: purity,
                constants.SEQUENZA_PLOIDY_KEY: ploidy
            }
        }
        return self._write_json(config, self.SEQUENZA_PARAMS_FILENAME)

class maf_extractor:

    def __init__(self, maf_path, bed_path):
        bed_cols = ['chrom', 'start', 'end']
        self.maf = pd.read_csv(maf_path, sep='\t', skiprows=1)
        self.bed = pd.read_csv(bed_path, sep='\t', skiprows=2, header=None, names=bed_cols)

    def find_tmb(self):
        target_space = sum(self.bed['end'] - self.bed['start']) / 1000000.0
        keep = ['Missense_Mutation', 'Frame_Shift_Del', 'In_Frame_Del', 'Frame_Shift_Ins',
                'In_Frame_Ins', 'Splice_Site', 'Translation_Start_Site', 'Nonsense_Mutation',
                'Nonstop_Mutation']
        tmb = len(self.maf.loc[self.maf["Variant_Classification"].isin(keep)]) / target_space
        return tmb
