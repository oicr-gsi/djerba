"""Extract and pre-process data, so it can be read into a clinical report JSON document"""

import csv
import json
import logging
import os
import pandas as pd
import re
import time
from shutil import copyfile

from djerba.extract.r_script_wrapper import r_script_wrapper
from djerba.extract.report_directory_parser import report_directory_parser
from djerba.sequenza import sequenza_reader
import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.util.logger import logger

class extractor(logger):
    """
    Extract the clinical report data from inptut configuration
    To start with, mostly a wrapper for the legacy R script singleSample.r
    Output: Directory of .txt and .tsv files for downstream processing
    Later on, will replace R script functionality with Python, and output JSON
    """

    CANCER_TYPE = 'cancer_type'
    CANCER_TYPE_DESCRIPTION = 'cancer_description'

    def __init__(self, config, report_dir, log_level=logging.WARNING, log_path=None):
        self.config = config
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.log_level = log_level
        self.log_path = log_path
        self.report_dir = report_dir
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', constants.DATA_DIR_NAME)
        self._check_sequenza_params()

    def _check_sequenza_params(self):
        """Check that configured purity/ploidy are consistent with Sequenza results; warn if not"""
        path = self.config.get(ini.DISCOVERED, ini.SEQUENZA_FILE)
        gamma = self.config.getint(ini.DISCOVERED, ini.SEQUENZA_GAMMA)
        solution = self.config.get(ini.DISCOVERED, ini.SEQUENZA_SOLUTION)
        self.logger.debug("Checking consistency of purity/ploidy; gamma={0}, solution={1}".format(gamma, solution))
        reader = sequenza_reader(path)
        purity = reader.get_purity(gamma, solution)
        configured_purity = self.config.getfloat(ini.DISCOVERED, ini.PURITY)
        ploidy = reader.get_ploidy(gamma, solution)
        configured_ploidy = self.config.getfloat(ini.DISCOVERED, ini.PLOIDY)
        if purity != configured_purity:
            msg = "Sequenza results path={0}, gamma={1}, solution={2} ".format(path, gamma, solution)+\
                "implies purity={0}, ".format(purity)+\
                "but INI configured purity={0}; ".format(configured_purity)+\
                "configured purity value will be used."
            self.logger.warning(msg)
        else:
            self.logger.debug("Purity OK")
        if ploidy != configured_ploidy:
            msg = "Sequenza results path={0}, gamma={1}, solution={2} ".format((path, gamma, solution))+\
                "implies purity={0}, ".format(purity)+\
                "but INI configured purity is {0}; ".format(configured_purity)+\
                "configured purity value will be used."
            self.logger.warning(msg)
        else:
            self.logger.debug("Ploidy OK")

    def _remove_oncotree_suffix(self, entry):
        """Remove a suffix of the form ' (PAAD)' or ' (AMLCBFBMYH11)' from an oncotree entry"""
        return re.sub(' \(\w+\)$', '', entry)

    def get_description(self):
        """
        Get cancer type and description from the oncotree file and code
        If nothing is found, warn and return empty strings
        """
        oncotree_path = self.config[ini.DISCOVERED][ini.ONCOTREE_DATA]
        oncotree_code = self.config[ini.INPUTS][ini.ONCOTREE_CODE]
        self.logger.info("Finding OncoTree info for code {0}".format(oncotree_code))
        # parse the oncotree file
        # if any of columns 1-7 contains the ONCOTREE_CODE (case-insensitive):
        # - column 1 has a CANCER_TYPE
        # - any column containing the ONCOTREE_CODE has a CANCER_TYPE_DESCRIPTION
        # - keep all distinct values of CANCER_TYPE and CANCER_TYPE_DESCRIPTION
        # - remove the suffix, eg. 'Astroblastoma (ASTB)' -> 'Astroblastoma'
        oncotree_regex = re.compile(oncotree_code, re.IGNORECASE)
        ct = set() # set of distinct CANCER_TYPE strings
        ctd = set() # set of distinct CANCER_TYPE_DESCRIPTION strings
        with open(oncotree_path) as oncotree_file:
            reader = csv.reader(oncotree_file, delimiter="\t")
            first = True
            for row in reader:
                if first: # skip the header row
                    first = False
                    continue
                for i in range(7):
                    if oncotree_regex.search(row[i]):
                        ct.add(self._remove_oncotree_suffix(row[0]))
                        ctd.add(self._remove_oncotree_suffix(row[i]))
        ct_str = '; '.join(sorted(list(ct)))
        ctd_str = '; '.join(sorted(list(ctd)))
        if len(ct)==0:
            self.logger.warning("Type not found in OncoTree for code {0}".format(oncotree_code))
        else:
            self.logger.info("Found {0} cancer type(s) in OncoTree: {1}".format(len(ct), ct_str))
        if len(ctd)==0:
            self.logger.warning("Description not found in OncoTree for code {0}".format(oncotree_code))
        else:
            self.logger.info("Found {0} cancer type description(s) in OncoTree: {1}".format(len(ctd), ctd_str))
        description = {
            self.CANCER_TYPE: ct_str,
            self.CANCER_TYPE_DESCRIPTION: ctd_str
        }
        return description

    def run(self, json_path=None, r_script=True):
        """Run extraction and write output"""
        self.logger.info("Djerba extract step started")
        if r_script:
            self.run_r_script() # can omit the R script for testing
        self.write_clinical_data(self.get_description())
        self.write_genomic_summary()
        self.write_analysis_unit()
        self.write_sequenza_meta()
        if json_path:
            self.write_json_summary(json_path)
        self.logger.info("Djerba extract step finished; extracted metrics written to {0}".format(self.report_dir))

    def run_r_script(self):
        wrapper = r_script_wrapper(
            self.config, self.report_dir, log_level=self.log_level, log_path=self.log_path
        )
        wrapper.run()

    def write_analysis_unit(self):
        """
        Write the analysis unit in its own (small) file
        Not needed for HTML generation, but used for the PDF report
        """
        out_path = os.path.join(self.report_dir, constants.ANALYSIS_UNIT_FILENAME)
        with open(out_path, 'w') as out_file:
            print(self.config[ini.DISCOVERED][ini.ANALYSIS_UNIT], file=out_file)

    def write_clinical_data(self, oncotree_info):
        """Write the data_clinical.txt file; based on legacy format from CGI-Tools"""
        purity = self.config[ini.DISCOVERED][ini.PURITY]
        ploidy = self.config[ini.DISCOVERED][ini.PLOIDY]
        req_approved_date = self.config[ini.INPUTS][ini.REQ_APPROVED_DATE]
        try:
            time.strptime(req_approved_date, "%Y/%m/%d")
        except ValueError as err:
            msg = "REQ_APPROVED_DATE '{0}' is not in YYYY/MM/DD format".format(req_approved_date)
            self.logger.error(msg)
            raise RuntimeError(msg) from err
        try:
            data = [
                ['PATIENT_LIMS_ID', self.config[ini.INPUTS][ini.PATIENT] ],
                ['PATIENT_STUDY_ID', self.config[ini.DISCOVERED][ini.PATIENT_ID] ],
                ['TUMOUR_SAMPLE_ID', self.config[ini.DISCOVERED][ini.TUMOUR_ID] ],
                ['BLOOD_SAMPLE_ID', self.config[ini.DISCOVERED][ini.NORMAL_ID] ],
                ['REPORT_VERSION', self.config[ini.INPUTS][ini.REPORT_VERSION] ],
                ['SAMPLE_TYPE', self.config[ini.INPUTS][ini.SAMPLE_TYPE] ],
                ['CANCER_TYPE', oncotree_info[self.CANCER_TYPE] ],
                ['CANCER_TYPE_DETAILED', self.config[ini.INPUTS][ini.ONCOTREE_CODE] ],
                ['CANCER_TYPE_DESCRIPTION', oncotree_info[self.CANCER_TYPE_DESCRIPTION] ],
                ['CLOSEST_TCGA', self.config[ini.INPUTS][ini.TCGA_CODE] ],
                ['SAMPLE_ANATOMICAL_SITE', self.config[ini.INPUTS][ini.SAMPLE_ANATOMICAL_SITE]],
                ['MEAN_COVERAGE', self.config[ini.INPUTS][ini.MEAN_COVERAGE] ],
                ['PCT_V7_ABOVE_80X', self.config[ini.INPUTS][ini.PCT_V7_ABOVE_80X] ],
                ['REQ_APPROVED_DATE', req_approved_date],
                ['SEQUENZA_PURITY_FRACTION', purity],
                ['SEQUENZA_PLOIDY', ploidy],
                ['SEX', self.config[ini.INPUTS][ini.SEX] ]
            ]
        except KeyError as err:
            msg = "Missing required clinical data value from config"
            raise KeyError(msg) from err
        # columns omitted from CGI-Tools format:
        # - DATE_SAMPLE_RECIEVED (has become REQ_APPROVED_DATE)
        # - SAMPLE_PRIMARY_OR_METASTASIS
        # - QC_STATUS
        # - QC_COMMENT
        # capitalization changed from CGI-Tools: PCT_v7_ABOVE_80x -> PCT_V7_ABOVE_80X
        head = "\t".join([x[0] for x in data])
        body = "\t".join([str(x[1]) for x in data])
        out_path = os.path.join(self.report_dir, constants.CLINICAL_DATA_FILENAME)
        with open(out_path, 'w') as out_file:
            print(head, file=out_file)
            print(body, file=out_file)

    def write_genomic_summary(self):
        """
        Copy a genomic_summary.txt file to the working directory
        File may have been manually configured; otherwise a default file is used
        (Long-term ambition is to generate the summary text automatically)
        """
        input_path = self.config[ini.DISCOVERED][ini.GENOMIC_SUMMARY]
        output_path = os.path.join(self.report_dir, constants.GENOMIC_SUMMARY_FILENAME)
        copyfile(input_path, output_path)

    def write_sequenza_meta(self):
        """
        Write a sequenza_meta.txt file to the working directory with metadata fields
        Metadata is not used directly for HTML/PDF generation, but kept for future reference
        """
        meta = {
            ini.SEQUENZA_FILE: self.config[ini.DISCOVERED][ini.SEQUENZA_FILE],
            ini.SEQUENZA_GAMMA: self.config[ini.DISCOVERED][ini.SEQUENZA_GAMMA],
            ini.SEQUENZA_REVIEWER_1: self.config[ini.INPUTS][ini.SEQUENZA_REVIEWER_1],
            ini.SEQUENZA_REVIEWER_2: self.config[ini.INPUTS][ini.SEQUENZA_REVIEWER_2],
            ini.SEQUENZA_SOLUTION: self.config[ini.DISCOVERED][ini.SEQUENZA_SOLUTION]
        }
        keys = sorted(list(meta.keys()))
        out_path = os.path.join(self.report_dir, constants.SEQUENZA_META_FILENAME)
        with open(out_path, 'w') as out_file:
            print("\t".join(keys), file=out_file)
            print("\t".join([str(meta[k]) for k in keys]), file=out_file)

    def write_json_summary(self, out_path):
        """Write a JSON summary of extracted data"""
        report_directory_parser(self.report_dir).write_json(out_path)

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
