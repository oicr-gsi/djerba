"""Pre-process data, so it can be read into a clinical report JSON document"""

import configparser
import json
import os

class processor:
    """
    Pre-process the clinical report data; replaces 4-singleSample.sh
    Input: INI config file from 3-configureSingleSample.sh
    Output: Directory of .txt and .json files for downstream processing
    """

    HEADER = 'REPORT_CONFIG'
    SAMPLE_INFO_KEY = 'sample_info'
    SAMPLE_PARAMS_FILENAME = 'sample_params.json'
    
    def __init__(self, iniPath, outDir):
        # INI section header is required by Python configparser, but not written by upstream script
        with open(iniPath) as iniFile:
            configString = "[%s]\n%s" % (self.HEADER, iniFile.read())
        self.config = configparser.ConfigParser()
        self.config.read_string(configString)
        if not os.path.exists(outDir):
            raise RuntimeError("Output path %s does not exist" % outDir)
        if not os.path.isdir(outDir):
            raise RuntimeError("Output path %s is not a directory" % outDir)
        if not os.access(outDir, os.W_OK):
            raise RuntimeError("Output path %s is not writable" % outDir)
        # TODO warn if outDir is not empty?
        self.outDir = outDir
        
    def run(self):
        """Run all processing and write output"""
        self.writeIniParams()

    def writeIniParams(self):
        """
        Take parameters directly from the config file, and write as JSON for later use
        Output approximates data_clinical.txt in CGI-Tools, but only has fields for final JSON output
        """
        sampleParams = {}
        sampleParams['PATIENT_ID'] = self.config[self.HEADER]['patientid'].strip('"')
        stringKeys = [
            'SAMPLE_TYPE',
            'CANCER_TYPE',
            'CANCER_TYPE_DETAILED',
            'CANCER_TYPE_DESCRIPTION',
            'DATE_SAMPLE_RECIEVED',
            'CLOSEST_TCGA',
            'SAMPLE_ANATOMICAL_SITE',
            'SAMPLE_PRIMARY_OR_METASTASIS',
            'QC_STATUS',
            'QC_COMMENT',
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
            sampleParams[key] = self.config[self.HEADER][key].strip('"')
        for key in floatKeys:
            sampleParams[key] = float(self.config[self.HEADER][key])
        with open(os.path.join(self.outDir, self.SAMPLE_PARAMS_FILENAME), 'w') as out:
            out.write(json.dumps({self.SAMPLE_INFO_KEY: sampleParams}, sort_keys=True, indent=4))
