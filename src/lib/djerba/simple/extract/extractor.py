"""Extract and pre-process data, so it can be read into a clinical report JSON document"""

import json
import os
import pandas as pd

from djerba.simple.extract.sequenza import sequenza_extractor
from djerba.simple.extract.r_script_wrapper import r_script_wrapper
import djerba.simple.constants as constants
import djerba.simple.ini_fields as ini

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

    # TODO
    # - only input is a ConfigParser object (updated using config_updater)
    # - get segfile path from sequenza reader, for rscript (using sequenza path from updater)
    # - get fusfile and gepfile paths from provenance, for rscript (via config updater)
    # - run the rscript
    # - parse rscript results into JSON for final collation

    def __init__(self, config):
        self.config = config
        self.work_dir = config[ini.SETTINGS][ini.SCRATCH_DIR]
        self.componentPaths = []

    def _write_json(self, config, fileName):
        outPath = os.path.join(self.work_dir, fileName)
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
        #self.componentPaths.append(self.writeConfigParams())

    def run_r_script(self):
        wrapper = r_script_wrapper(config)
        wrapper.run()

    def writeConfigParams(self):
        """
        Take parameters directly from extraction config, and write as JSON for later use
        Output approximates data_clinical.txt in CGI-Tools, but only has fields for final JSON output
        """
        # TODO simplify and take params from INI config
        # may introduce an 'attributes' INI section for params which will be carried forward unchanged
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
        maf_path = self.config[ini.DISCOVERED][ini.MAF_FILE]
        tmb = maf_extractor(maf_path, self.config[ini.SETTINGS][ini.BED_PATH]).find_tmb()
        config = {
            constants.READER_CLASS_KEY: 'json_reader',
            self.SAMPLE_INFO_KEY: {
                constants.TMB_PER_MB_KEY: tmb
            }
        }
        return self._write_json(config, self.MAF_PARAMS_FILENAME)

    def writeSequenzaParams(self):
        """Read the Sequenza results.zip, extract relevant parameters, and write as JSON"""
        ex = sequenza_extractor(self.config[ini.DISCOVERED][ini.SEQUENZA_FILE])
        gamma = self.config.getint(ini.INPUTS, ini.GAMMA)
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
