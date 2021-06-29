"""Extract and pre-process data, so it can be read into a clinical report JSON document"""

import json
import os
import pandas as pd

from djerba.extract.sequenza import sequenza_extractor
from djerba.extract.r_script_wrapper import r_script_wrapper
import djerba.util.constants as constants
import djerba.util.ini_fields as ini

class extractor:
    """
    Extract the clinical report data from inptut configuration
    To start with, mostly a wrapper for the legacy R script singleSample.r
    Output: Directory of .txt and .tsv files for downstream processing
    Later on, will replace R script functionality with Python, and output JSON
    """

    # TODO extract clinical data from config and write to data_clinical.txt

    SAMPLE_INFO_KEY = 'sample_info'
    CLINICAL_DATA_FILENAME = 'data_clinical.txt'
    SAMPLE_META_PARAMS_FILENAME = 'sample_meta_params.json'
    MAF_PARAMS_FILENAME = 'maf_params.json'
    SEQUENZA_PARAMS_FILENAME = 'sequenza_params.json'

    def __init__(self, config, work_dir=None):
        self.config = config
        if work_dir == None:
            self.work_dir = config[ini.SETTINGS][ini.EXTRACTION_DIR]
        else:
            self.work_dir = work_dir

    def _write_json(self, data, out_path):
        with open(out_path, 'w') as out:
            out.write(json.dumps(data, sort_keys=True, indent=4))
        return out_path

    def get_sequenza_params(self):
        """Read the Sequenza results.zip, extract relevant parameters, and write as JSON"""
        ex = sequenza_extractor(self.config[ini.DISCOVERED][ini.SEQUENZA_FILE])
        gamma = self.config.getint(ini.INPUTS, ini.GAMMA)
        [purity, ploidy] = ex.get_purity_ploidy(gamma) # if gamma==None, this uses the default
        params = {
            constants.SEQUENZA_GAMMA: gamma,
            constants.SEQUENZA_PURITY_KEY: purity,
            constants.SEQUENZA_PLOIDY_KEY: ploidy
        }
        return params

    def run(self, json_path=None, r_script=True):
        """Run extraction and write output"""
        if r_script:
            self.run_r_script() # can omit the R script for testing
        self.write_clinical_data(self.get_sequenza_params())
        if json_path:
            self.write_json_summary(json_path)

    def run_r_script(self):
        wrapper = r_script_wrapper(self.config)
        wrapper.run()

    def write_clinical_data(self, sequenza_params):
        """Write the data_clinical.txt file; based on legacy format from CGI-Tools"""
        purity = sequenza_params[constants.SEQUENZA_PURITY_KEY]
        ploidy = sequenza_params[constants.SEQUENZA_PLOIDY_KEY]
        # TODO move config values from inputs to sample_meta?
        try:
            data = [
                ['PATIENT_LIMS_ID', self.config[ini.INPUTS][ini.PATIENT] ],
                ['PATIENT_STUDY_ID', self.config[ini.INPUTS][ini.PATIENT_ID] ],
                ['TUMOR_SAMPLE_ID', self.config[ini.INPUTS][ini.TUMOUR_ID] ],
                ['BLOOD_SAMPLE_ID', self.config[ini.INPUTS][ini.NORMAL_ID] ],
                ['REPORT_VERSION', self.config[ini.SAMPLE_META][ini.REPORT_VERSION] ],
                ['SAMPLE_TYPE', self.config[ini.SAMPLE_META][ini.SAMPLE_TYPE] ],
                ['CANCER_TYPE', self.config[ini.SAMPLE_META][ini.CANCER_TYPE] ],
                ['CANCER_TYPE_DETAILED', self.config[ini.INPUTS][ini.CANCER_TYPE_DETAILED] ],
                ['CANCER_TYPE_DESCRIPTION', self.config[ini.SAMPLE_META][ini.CANCER_TYPE_DESCRIPTION] ],
                ['CLOSEST_TCGA', self.config[ini.INPUTS][ini.TCGA_CODE] ],
                ['SAMPLE_ANATOMICAL_SITE', self.config[ini.SAMPLE_META][ini.SAMPLE_ANATOMICAL_SITE]],
                ['MEAN_COVERAGE', self.config[ini.SAMPLE_META][ini.MEAN_COVERAGE] ],
                ['PCT_V7_ABOVE_80X', self.config[ini.SAMPLE_META][ini.PCT_V7_ABOVE_80X] ],
                ['SEQUENZA_PURITY_FRACTION', purity],
                ['SEQUENZA_PLOIDY', ploidy],
                ['SEX', self.config[ini.SAMPLE_META][ini.SEX] ]
            ]
        except KeyError as err:
            msg = "Missing required clinical data value from config"
            raise KeyError(msg) from err
        # columns omitted from CGI-Tools format, as they are not in use for R markdown:
        # - DATE_SAMPLE_RECIEVED
        # - SAMPLE_PRIMARY_OR_METASTASIS
        # - QC_STATUS
        # - QC_COMMENT
        # capitalization changed from CGI-Tools: PCT_v7_ABOVE_80x -> PCT_V7_ABOVE_80X
        head = "\t".join([x[0] for x in data])
        body = "\t".join([str(x[1]) for x in data])
        out_path = os.path.join(self.work_dir, self.CLINICAL_DATA_FILENAME)
        with open(out_path, 'w') as out_file:
            print(head, file=out_file)
            print(body, file=out_file)

    def write_json_summary(self, out_path):
        """Write a JSON summary of extracted data"""
        # TODO write summary, in keeping with an updated Elba schema
        # for now, this is just a placeholder
        # TODO log status instead of printing to STDOUT
        print('### placeholder; JSON summary not yet implemented')
        data = {
            'summary': 'JSON summary goes here'
        }
        return self._write_json(data, out_path)

class maf_extractor:

    """
    Class for extracting MAF stats using Python
    """
    # Proof-of-concept; not in production for release 0.0.5
    # TODO expand and use to replace relevant outputs from R script

    def __init__(self, maf_path, bed_path):
        bed_cols = ['chrom', 'start', 'end']
        # low_memory=False is to suppress DtypeWarning
        # TODO specify dtypes, see: https://stackoverflow.com/questions/24251219/pandas-read-csv-low-memory-and-dtype-options
        self.maf = pd.read_csv(maf_path, sep='\t', skiprows=1, low_memory=False)
        self.bed = pd.read_csv(bed_path, sep='\t', skiprows=2, header=None, names=bed_cols)

    def find_tmb(self):
        target_space = sum(self.bed['end'] - self.bed['start']) / 1000000.0
        keep = ['Missense_Mutation', 'Frame_Shift_Del', 'In_Frame_Del', 'Frame_Shift_Ins',
                'In_Frame_Ins', 'Splice_Site', 'Translation_Start_Site', 'Nonsense_Mutation',
                'Nonstop_Mutation']
        tmb = len(self.maf.loc[self.maf["Variant_Classification"].isin(keep)]) / target_space
        return tmb
