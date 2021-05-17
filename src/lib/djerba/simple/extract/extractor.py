"""Extract and pre-process data, so it can be read into a clinical report JSON document"""

import json
import os
import djerba.simple.constants as constants

class extractor:
    """
    Extract the clinical report data; replaces 4-singleSample.sh
    Input: INI config from 3-configureSingleSample.sh
    Output: Directory of .txt and .json files for downstream processing
    """

    SAMPLE_INFO_KEY = 'sample_info'
    SAMPLE_PARAMS_FILENAME = 'sample_params.json'
    MAF_PARAMS_FILENAME = 'maf_params.json'
    
    def __init__(self, config, outDir):
        # config is a ConfigParser object with required parameters (eg. from INI file)
        # INI section header is required by Python configparser, but not written by upstream script
        self.config = config
        self.outDir = outDir
        self.configPaths = []

    def _write_json(self, config, fileName):
        outPath = os.path.join(self.outDir, fileName)
        with open(outPath, 'w') as out:
            out.write(json.dumps(config, sort_keys=True, indent=4))
        return outPath

    def getConfigPaths(self):
        """JSON configuration paths to create reader objects and build the report"""
        return self.configPaths

    def run(self):
        """Run all extractions and write output"""
        self.configPaths.append(self.writeMafParams())
        self.configPaths.append(self.writeIniParams())

    def writeIniParams(self):
        """
        Take parameters directly from the config file, and write as JSON for later use
        Output approximates data_clinical.txt in CGI-Tools, but only has fields for final JSON output
        """
        sampleParams = {}
        sampleParams['PATIENT_ID'] = self.config[constants.CONFIG_HEADER]['patientid'].strip('"')
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
            sampleParams[key] = self.config[constants.CONFIG_HEADER][key].strip('"')
        for key in floatKeys:
            sampleParams[key] = float(self.config[constants.CONFIG_HEADER][key])
        config = {
            constants.READER_CLASS_KEY: 'json_reader',
            self.SAMPLE_INFO_KEY: sampleParams
        }
        return self._write_json(config, self.SAMPLE_PARAMS_FILENAME)

    def writeMafParams(self):
        """Read the MAF file, extract relevant parameters, and write as JSON"""
        config = {
            constants.READER_CLASS_KEY: 'json_reader',
            self.SAMPLE_INFO_KEY: {
                constants.TMB_PER_MB_KEY: 'TMB_PER_MB_placeholder'
            }
        }
        return self._write_json(config, self.MAF_PARAMS_FILENAME)
