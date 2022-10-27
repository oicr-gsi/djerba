"""Extract and pre-process data, so it can be read into a clinical report JSON document"""

import csv
import json
import logging
import os
import pandas as pd
import re
import time
from shutil import copyfile
import numpy
from djerba.extract.report_to_json import clinical_report_json_composer
from djerba.extract.r_script_wrapper import r_script_wrapper
from djerba.sequenza import sequenza_reader
import djerba.extract.constants as xc
import djerba.render.constants as render_constants
import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger

class extractor(logger):
    """
    Extract the clinical report data from input configuration
    Includes a wrapper for the legacy R script singleSample.r
    Output:
    - "Report directory" of .txt and .tsv files
    - JSON file derived from report directory, for archiving and HTML rendering
    """

    CANCER_TYPE = 'cancer_type'
    CANCER_TYPE_DESCRIPTION = 'cancer_description'

    def __init__(self, config, report_dir, author, wgs_only, failed, depth,
                 log_level=logging.WARNING, log_path=None):
        self.config = config
        self.author = author
        self.wgs_only = wgs_only
        if self.wgs_only:
            self.assay_type = render_constants.ASSAY_WGS
        else:
            self.assay_type = render_constants.ASSAY_WGTS
        self.failed = failed
        self.depth = depth
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.converter = converter(log_level, log_path)
        if self.failed:
            self.logger.info("Extracting Djerba data for failed report")
        elif self.wgs_only:
            self.logger.info("Extracting Djerba data for WGS-only report")
        else:
            self.logger.info("Extracting Djerba data for WGS+WTS report")
        self.report_dir = report_dir
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', constants.DATA_DIR_NAME)
        if self.failed:
            self.logger.debug("Failed report mode; omitting check on sequenza params")
        else:
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
            msg = "Sequenza results path={0}, gamma={1}, solution={2} ".format(path, gamma, solution)+\
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
        # match against uppercase ONCOTREE_CODE in parentheses, eg. '(ETT)', not 'ett'
        # if any of columns 1-7 matches):
        # - column 1 has a CANCER_TYPE
        # - any column containing the ONCOTREE_CODE has a CANCER_TYPE_DESCRIPTION
        # - expect exactly one distinct value each, for CANCER_TYPE and CANCER_TYPE_DESCRIPTION
        # - remove the suffix, eg. 'Astroblastoma (ASTB)' -> 'Astroblastoma'
        oncotree_regex = re.compile('\({0}\)'.format(oncotree_code.upper()))
        ct = set() # set of distinct CANCER_TYPE strings
        ctd = set() # set of distinct CANCER_TYPE_DESCRIPTION strings
        with open(oncotree_path) as oncotree_file:
            oncotree_file.readline() # skip the header row
            reader = csv.reader(oncotree_file, delimiter="\t")
            for row in reader:
                for i in range(7):
                    if oncotree_regex.search(row[i]):
                        ct.add(self._remove_oncotree_suffix(row[0]))
                        ctd.add(self._remove_oncotree_suffix(row[i]))
        placeholder = 'UNKNOWN'
        if len(ct) != 1:
            found = ct if len(ct)>1 else 'no entries'
            msg = "Cannot find unique cancer type from OncoTree code {0}; found {1}; substituting {2}".format(oncotree_code, found, placeholder)
            self.logger.warning(msg)
            ct_str = placeholder
        else:
            ct_str = ct.pop()
        if len(ctd) != 1:
            found = ctd if len(ctd)>1 else 'no entries'
            msg = "Cannot find unique cancer description from OncoTree code {0}; found {1}; substituting {2}".format(oncotree_code, found, placeholder)
            self.logger.warning(msg)
            ctd_str = placeholder
        else:
            ctd_str = ctd.pop()
        description = {
            self.CANCER_TYPE: ct_str,
            self.CANCER_TYPE_DESCRIPTION: ctd_str
        }
        return description

    def run(self, r_script=True):
        """Run extraction and write output"""
        self.logger.info("Djerba extract step started")
        if self.failed:
            self.logger.info("Failed report mode, writing clinical data and genomic summary only")
        else:
            self.logger.info("Extracting metrics to report directory")
            if r_script:
                self.run_r_script() # can omit the R script for testing
            self.write_sequenza_meta()
        self.write_clinical_data(self.get_description())
        self.preprocess_msi(self.config[ini.DISCOVERED][ini.MSI_FILE], self.report_dir)
        self.write_genomic_summary()
        self.write_technical_notes()
        params = {
            xc.AUTHOR: self.author,
            xc.ASSAY_TYPE: self.assay_type,
            xc.ASSAY_NAME: self.config[ini.INPUTS][ini.ASSAY_NAME],
            xc.COVERAGE: self.depth,
            xc.FAILED: self.failed,
            xc.ONCOTREE_CODE: self.config[ini.INPUTS][ini.ONCOTREE_CODE],
            xc.PURITY_FAILURE: False, # TODO populate from config
            xc.STUDY: self.config[ini.INPUTS][ini.STUDY_ID]
        }
        report_data = clinical_report_json_composer(
            self.report_dir,
            params,
            self.log_level,
            self.log_path
        ).run()
        self.write_json(report_data)
        self.logger.info("Djerba extract step finished; extracted metrics written to {0}".format(self.report_dir))

    def run_r_script(self):
        wrapper = r_script_wrapper(
            self.config, self.report_dir, self.wgs_only, log_level=self.log_level, log_path=self.log_path
        )
        wrapper.run()

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
                [constants.PATIENT_LIMS_ID, self.config[ini.INPUTS][ini.PATIENT] ],
                [constants.PATIENT_STUDY_ID, self.config[ini.DISCOVERED][ini.PATIENT_ID] ],
                [constants.TUMOUR_SAMPLE_ID, self.config[ini.DISCOVERED][ini.TUMOUR_ID] ],
                [constants.BLOOD_SAMPLE_ID, self.config[ini.DISCOVERED][ini.NORMAL_ID] ],
                [constants.REPORT_VERSION, self.config[ini.INPUTS][ini.REPORT_VERSION] ],
                [constants.SAMPLE_TYPE, self.config[ini.INPUTS][ini.SAMPLE_TYPE] ],
                [constants.CANCER_TYPE, oncotree_info[self.CANCER_TYPE] ],
                [constants.CANCER_TYPE_DETAILED, self.config[ini.INPUTS][ini.ONCOTREE_CODE] ],
                [constants.CANCER_TYPE_DESCRIPTION, oncotree_info[self.CANCER_TYPE_DESCRIPTION] ],
                [constants.CLOSEST_TCGA, self.config[ini.INPUTS][ini.TCGA_CODE] ],
                [constants.SAMPLE_ANATOMICAL_SITE, self.config[ini.INPUTS][ini.SAMPLE_ANATOMICAL_SITE]],
                [constants.MEAN_COVERAGE, self.config[ini.INPUTS][ini.MEAN_COVERAGE] ],
                [constants.PCT_V7_ABOVE_80X, self.config[ini.INPUTS][ini.PCT_V7_ABOVE_80X] ],
                [constants.REQ_APPROVED_DATE, req_approved_date],
                [constants.SEQUENZA_PURITY_FRACTION, purity],
                [constants.SEQUENZA_PLOIDY, ploidy],
                [constants.SEX, self.config[ini.INPUTS][ini.SEX] ]
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

    def preprocess_msi(self, msi_path, report_dir):
        """
        summarize msisensor file
        """
        out_path = os.path.join(report_dir, 'msi.txt')
        msi_boots = []
        with open(msi_path, 'r') as msi_file:
            reader_file = csv.reader(msi_file, delimiter="\t")
            for row in reader_file:
                msi_boots.append(float(row[3]))
        msi_perc = numpy.percentile(numpy.array(msi_boots), [0, 25, 50, 75, 100])
        with open(out_path, 'w') as out_file:
            for item in list(msi_perc):
                out_file.write(str(str(item)+"\t"))
        return out_path

    def write_genomic_summary(self):
        """
        Copy a genomic_summary.txt file to the working directory
        File may have been manually configured; otherwise a default file is used
        (Long-term ambition is to generate the summary text automatically)
        """
        input_path = self.config[ini.DISCOVERED][ini.GENOMIC_SUMMARY]
        output_path = os.path.join(self.report_dir, constants.GENOMIC_SUMMARY_FILENAME)
        copyfile(input_path, output_path)
        
    def write_technical_notes(self):
        """
        Copy a technical_notes.txt file to the working directory
        File may have been manually configured; otherwise a default file is used
        """
        input_path = self.config[ini.DISCOVERED][ini.TECHNICAL_NOTES]
        output_path = os.path.join(self.report_dir, constants.TECHNICAL_NOTES_FILENAME)
        copyfile(input_path, output_path)

    def write_json(self, report_data):
        """
        Write the main JSON file with 'report' and 'supplementary' sections
        """
        # convert the ConfigParser INI to a dictionary for output
        config_data = {}
        for section in self.config.sections():
            config_data[section] = {}
            for key, val in self.config.items(section):
                if re.match('^-*[0-9]+\.[0-9]+$', val):
                    val = float(val)
                elif re.match('^-*[0-9]+$', val):
                    val = int(val)
                config_data[section][key] = val
        # shorter key names
        tmb_key = render_constants.TMB_PLOT
        vaf_key = render_constants.VAF_PLOT
        logo_key = render_constants.OICR_LOGO
        # machine-readable; replace image paths with base-64 blobs for a self-contained document
        report_data[logo_key] = self.converter.convert_png(report_data[logo_key], 'OICR logo')
        if not self.failed:
            report_data[tmb_key] = self.converter.convert_svg(report_data[tmb_key], 'TMB plot')
            report_data[vaf_key] = self.converter.convert_svg(report_data[vaf_key], 'VAF plot')
        report_path = os.path.join(self.report_dir, constants.REPORT_JSON_FILENAME)
        data = {
            constants.REPORT: report_data,
            constants.SUPPLEMENTARY: {
                constants.CONFIG: config_data
            }
        }
        with open(report_path, 'w') as out_file:
            print(json.dumps(data), file=out_file)
        self.logger.debug('Wrote JSON report to {0}'.format(report_path))

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
