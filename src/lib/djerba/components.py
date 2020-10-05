"""Classes to represent components of a cBioPortal study

Eg. study metadata, clinical sample/patient data, pipeline outputs
"""

import logging
import os
import pandas as pd
import re
import yaml

from djerba.utilities.base import base
import djerba.utilities.constants

class component(base):

    """
    Base class for data/metadata components of a cBioPortal study
    Eg. Study metadata, clinical sample/patient data, pipeline output
    Subclasses can call super().__init__() to set up simple logging
    """

    def __init__(self, log_level=logging.WARN):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__))

    def write(self, out_dir):
        msg = "Placeholder write() method of base class, should not be called"
        self.logger.error(msg)
        raise RuntimeError(msg)

class dual_output_component(component):

    """
    Base class for components with separate data and metadata files
    """

    def write_data(self, out_dir):
        msg = "Placeholder write_data() method of base class, should not be called"
        self.logger.error(msg)
        raise RuntimeError(msg)
        
    def write_meta(self, out_dir):
        msg = "Placeholder write_meta() method of base class, should not be called"
        self.logger.error(msg)
        raise RuntimeError(msg)
        
    def write(self, out_dir):
        self.write_data(out_dir)
        self.write_meta(out_dir)


class cancer_type(dual_output_component):

    """cancer_type component, including dedicated colours and type_of_cancer from study"""

    DATATYPE = djerba.utilities.constants.CANCER_TYPE_DATATYPE
    DATA_FILENAME = 'data_cancer_type.txt'
    META_FILENAME = 'meta_cancer_type.txt'
    COLOUR_FILENAME = 'cancer_colours.csv'
    DEFAULT_COLOUR = 'lavender' # default colour for general cancer awareness

    COLOR_KEY = 'dedicated_color'
    DATA_FILENAME_KEY = 'data_filename_key'
    KEYWORDS_KEY = 'clinical_trial_keywords'
    NAME_KEY = 'name'
    PARENT_KEY = 'parent_type_of_cancer'
    TYPE_OF_CANCER_KEY = 'type_of_cancer'

    def __init__(self, config, default_cancer_type_string=None, log_level=logging.WARN):
        super().__init__(log_level)
        # default_cancer_type_string is from study metadata, may be used for "type_of_cancer" field
        self.config = config
        # check config fields are consistent in length
        self.rows = len(config.get(self.NAME_KEY))
        for key in [self.KEYWORDS_KEY, self.PARENT_KEY, self.COLOR_KEY, self.TYPE_OF_CANCER_KEY]:
            value = config.get(key)
            if key in [self.COLOR_KEY, self.TYPE_OF_CANCER_KEY] and value == None:
                pass # these values may be null
            elif len(config.get(key)) != self.rows:
                msg = "Incorrect number of fields for cancer_type config key %s" % key
                self.logger.error(msg)
                raise ValueError(msg)
        # generate the 'type_of_cancer' column
        if config.get(self.TYPE_OF_CANCER_KEY):
            self.type_of_cancer_column = config.get(self.TYPE_OF_CANCER_KEY)
        else:
            self.type_of_cancer_column = [default_cancer_type_string]*self.rows
        # generate the 'colours' column; attempt to find a matching colour in reference file
        if config.get(self.COLOR_KEY):
            self.colours_column = config.get(self.COLOR_KEY)
        else:
            # read colours reference as a pandas dataframe
            ref_path = os.path.join(
                os.path.dirname(__file__),
                djerba.utilities.constants.DATA_DIRNAME,
                self.COLOUR_FILENAME
            )
            colours = pd.read_csv(ref_path)
            self.colours_column = []
            for name in config.get(self.NAME_KEY):
                # use .casefold() instead of .lower() to handle special cases
                name_expr = re.compile(name.casefold())
                candidate_colours = []
                for index, row in colours.iterrows():
                    ref_name = row['NAME']
                    if name_expr.search(ref_name.casefold()):
                        candidate_colours.append(row['COLOUR'])
                distinct_colour_total = len(set(candidate_colours))
                if distinct_colour_total == 0:
                    colour = self.DEFAULT_COLOUR_NAME
                elif distinct_colour_total == 1:
                    colour = candidate_colours[0].casefold()
                else:
                    colour = self.DEFAULT_COLOUR_NAME
                    msg = "Conflicting colour values found for cancer name "+\
                          "'%s', defaulting to '%s'" % (name, colour)
                    self.logger.warning(msg)
                self.colours_column.append(colour)

    def write_data(self, out_dir):
        out = open(os.path.join(out_dir, self.DATA_FILENAME), 'w')
        for i in range(self.rows):
            values = [
                self.type_of_cancer_column[i],          # type_of_cancer
                self.config.get(self.NAME_KEY)[i],      # name
                self.config.get(self.KEYWORDS_KEY)[i],  # clinical_trial_keywords
                self.colours_column[i],                 # dedicated_color
                self.config.get(self.PARENT_KEY)[i],    # parent_type_of_cancer
            ]
            print("\t".join(values), file=out)
        out.close()

    def write_meta(self, out_dir):
        meta = {}
        meta['genetic_alteration_type'] = self.DATATYPE
        meta['datatype'] = self.DATATYPE
        meta['data_filename'] = self.DATA_FILENAME
        out = open(os.path.join(out_dir, self.META_FILENAME), 'w')
        out.write(yaml.dump(meta, sort_keys=True))
        out.close()

class case_list(component):

    CATEGORY_KEY = 'category'
    NAME_KEY = 'case_list_name'
    DESC_KEY = 'case_list_description'

    SUFFIX_KEY = 'suffix'
    CASE_LIST_NAME_KEY = 'case_list_name'
    CASE_LIST_DESCRIPTION_KEY = 'case_list_description'
    CASE_LIST_IDS_KEY = 'case_list_ids'
    CASE_LIST_CATEGORY_KEY = 'case_list_category'

    def __init__(self, study_id, config, log_level=logging.WARN):
        super().__init__(log_level)
        self.cancer_study_identifier = study_id
        self.suffix = config[self.SUFFIX_KEY]
        self.stable_id = "%s_%s" % (study_id, self.suffix)
        self.case_list_name = config[self.CASE_LIST_NAME_KEY]
        self.case_list_description = config[self.CASE_LIST_DESCRIPTION_KEY]
        self.sample_ids = config[self.CASE_LIST_IDS_KEY]
        self.category = config.get(self.CASE_LIST_CATEGORY_KEY, None)

    def write(self, out_dir):
        data = {}
        data['cancer_study_identifier'] = self.cancer_study_identifier
        data['stable_id'] = self.stable_id
        data[self.NAME_KEY] = self.case_list_name
        data[self.DESC_KEY] = self.case_list_description
        data['case_list_ids'] = "\t".join(self.sample_ids)
        if self.category != None:
            data[self.CATEGORY_KEY] = self.category
        out_path = os.path.join(out_dir, 'cases_%s.txt' % self.suffix)
        if os.path.exists(out_path):
            msg = "Output path already exists; not overwriting; "+\
                  "case list suffix %s may not be unique" % self.suffix
            self.logger.warn(msg)
        out = open(out_path, 'w')
        for key in data.keys():
            # not using YAML dump; we want a literal tab-delimited string, not YAML representation
            print("%s: %s" % (key, data[key]), file=out)
        out.close()
    
        
class clinical_data_component(dual_output_component):

    """Clinical patient/sample data in a cBioPortal study"""

    DATATYPE = '_placeholder_'
    DATA_FILENAME = '_data_placeholder_'
    META_FILENAME = '_meta_placeholder_'
    DEFAULT_PRECISION = 3
    
    ATTRIBUTE_NAMES_KEY = 'attribute_names'
    DATATYPES_KEY = 'datatypes'
    DESCRIPTIONS_KEY = 'descriptions'
    DISPLAY_NAMES_KEY = 'display_names'
    PRIORITIES_KEY = 'priorities'
    PRECISION_KEY = 'precision'

    def __init__(self, samples, samples_meta, study_id, log_level=logging.WARN):
        super().__init__(log_level)
        self.cancer_study_identifier = study_id
        self.samples = samples
        self.samples_meta = samples_meta
        self.precision = self.samples_meta.get(self.PRECISION_KEY, self.DEFAULT_PRECISION)

    def write_data(self, out_dir):
        """Write header; then write selected attributes of samples"""
        out = open(os.path.join(out_dir, self.DATA_FILENAME), 'w')
        attribute_names = self.samples_meta[self.ATTRIBUTE_NAMES_KEY]
        self.logger.debug("Writing data file header for %s" % self.DATATYPE)
        print("#"+"\t".join(self.samples_meta[self.DISPLAY_NAMES_KEY]), file=out)
        print("#"+"\t".join(self.samples_meta[self.DESCRIPTIONS_KEY]), file=out)
        print("#"+"\t".join(self.samples_meta[self.DATATYPES_KEY]), file=out)
        print("#"+"\t".join([str(x) for x in self.samples_meta[self.PRIORITIES_KEY]]), file=out)
        print("#"+"\t".join(attribute_names), file=out)
        self.logger.debug("Writing data file table for %s" % self.DATATYPE)
        for sample in self.samples:
            fields = []
            for name in attribute_names:
                value = sample.get(name)
                if value == None:
                    field = 'NULL' # interpreted as NaN by pandas
                elif isinstance(value, float):
                    format_str = "%.{}f".format(self.precision)
                    field = format_str % value
                else:
                    field = str(value)
                fields.append(field)
            print("\t".join(fields), file=out)
        out.close()

    def write_meta(self, out_dir):
        meta = {}
        meta['cancer_study_identifier'] = self.cancer_study_identifier
        meta['genetic_alteration_type'] = 'CLINICAL'
        meta['datatype'] = self.DATATYPE
        meta['data_filename'] = self.DATA_FILENAME
        out = open(os.path.join(out_dir, self.META_FILENAME), 'w')
        out.write(yaml.dump(meta, sort_keys=True))
        out.close()

class patients_component(clinical_data_component):

    DATATYPE = djerba.utilities.constants.PATIENT_DATATYPE
    DATA_FILENAME = 'data_clinical_patients.txt'
    META_FILENAME = 'meta_clinical_patients.txt'

class samples_component(clinical_data_component):

    DATATYPE = djerba.utilities.constants.SAMPLE_DATATYPE
    DATA_FILENAME = 'data_clinical_samples.txt'
    META_FILENAME = 'meta_clinical_samples.txt'


class study_meta(component):

    """Metadata for the study; no data in this component"""

    META_FILENAME = 'meta_study.txt'

    def __init__(self, study_meta, log_level=logging.WARN):
        super().__init__(log_level)
        self.study_meta = study_meta

    def get(self, key):
        return self.study_meta.get(key)

    def write(self, out_dir):
        meta = {}
        for field in djerba.utilities.constants.REQUIRED_STUDY_META_FIELDS:
            try:
                meta[field] = self.study_meta[field]
            except KeyError:
                msg = "Missing required study meta field "+field
                self.logger.error(msg)
                raise
        for field in djerba.utilities.constants.OPTIONAL_STUDY_META_FIELDS:
            if self.study_meta.get(field):
                meta[field] = self.study_meta[field]
        out = open(os.path.join(out_dir, self.META_FILENAME), 'w')
        out.write(yaml.dump(meta, sort_keys=True))
        out.close()
