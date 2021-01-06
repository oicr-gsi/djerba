"""Genome interpretation Clinical Report configuration"""

import couchdb2
import json
import jsonschema
import logging
import os
import sys
from math import isnan
from jsonschema.exceptions import ValidationError, SchemaError
from djerba.genetic_alteration import genetic_alteration_factory
from djerba.sample import sample
from djerba.utilities import constants
from djerba.utilities.base import base

class uploader(base):
    """Class to validate report config and upload to an Elba instance"""

    ID_KEY = "_id" # reserved key to identify CouchDB documents

    # Elba upload config
    UPLOAD_CONFIG_FILENAME = 'upload_config.json'
    DB_NAME_KEY = 'db_name'
    DB_PORT_KEY = 'db_port'
    DB_URL_KEY = 'db_url'

    def __init__(self, schema_path=None, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.schema = self.get_schema(schema_path)

    def get_schema(self, schema_path):
        if schema_path:
            with open(schema_path, 'r') as schema_file:
                self.schema = json.loads(schema_file.read())
        else:
            self.schema = None
        return self.schema

    def upload(self, config_input, upload_config=None, report_id=None):
        """Upload report configuration to an Elba database"""
        config = config_input.copy() # avoid modifying the original input as a side effect
        if not upload_config:
            upload_config_path = os.path.join(
                os.path.dirname(__file__),
                constants.DATA_DIRNAME,
                self.UPLOAD_CONFIG_FILENAME
            )
            self.logger.info("Loading default Elba DB config from %s" % upload_config_path)
            with open(upload_config_path, 'r') as in_file:
                upload_config = json.loads(in_file.read())
        db_url = upload_config.get(self.DB_URL_KEY)
        db_port = upload_config.get(self.DB_PORT_KEY)
        db_name = upload_config.get(self.DB_NAME_KEY)
        db_user = os.environ.get(constants.ELBA_DB_USER)
        db_pass = os.environ.get(constants.ELBA_DB_PASSWORD)
        if not (db_user and db_pass):
            msg = "Username and password for Elba database must be stored as environment variables "+\
                  "%s and %s, respectively." % (constants.ELBA_DB_USER, constants.ELBA_DB_PASSWORD)
            self.logger.error(msg)
            raise DjerbaReportError(msg)
        db_req = "http://%s:%s@%s:%s/" % (db_user, db_pass, db_url, db_port)
        try:
            db = couchdb2.Server(db_req).get(db_name)
        except Error as err:
            msg = "Failed to open Elba database '{0}' at {1}: {2}".format(db_name, db_url, err)
            self.logger.error(msg)
            raise DjerbaReportError(msg) from err
        self.logger.info("Opened connection to Elba database at {}".format(db_url))
        # check the ID_KEY entry; if not present, CouchDB will create one
        if self.ID_KEY in config:
            msg = "Elba config is not permitted to use reserved key %s" % self.ID_KEY
            self.logger.error(msg)
            raise DjerbaReportError(msg)
        elif report_id:
            config[self.ID_KEY] = report_id
            self.logger.debug("Using report ID '%s' for Elba database" % report_id)
        else:
            self.logger.debug("Using automatically-generated default ID in Elba database")
        db.put(config)
        self.logger.info("Uploaded config to Elba server")

    def validate(self, config):
        if self.schema:
            try:
                jsonschema.validate(config, self.schema)
                self.logger.info("Elba config is valid with respect to schema")
            except (ValidationError, SchemaError) as err:
                msg = "Elba config is invalid with respect to schema"
                self.logger.error("{}: {}".format(msg, err))
                debug_msg = "Invalid Elba config output:\n"+\
                            json.dumps(config, sort_keys=True, indent=4)
                self.logger.debug(debug_msg)
                raise
        else:
            self.logger.info("Elba config schema not available; validation omitted")

class report(uploader):

    """
    Class representing a genome interpretation Clinical Report in Elba

    Inherits upload and validation methods from the parent class
    """

    NULL_STRING = "NA"

    def __init__(self, config, sample_id=None, schema_path=None, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.schema = self.get_schema(schema_path)
        # configure the sample for the report
        if sample_id==None: # only one sample
            if len(config[constants.SAMPLES_KEY])==1:
                self.sample = sample(config[constants.SAMPLES_KEY][0], log_level)
                self.sample_id = self.sample.get_id()
            else:
                msg = "Config contains multiple samples; must specify which one to use in report"
                self.logger.error(msg)
                raise DjerbaReportError(msg)
        else: # multiple samples, see if the requested sample_id is present
            self.sample_id = sample_id
            report_sample = None
            for sample_config in config[constants.SAMPLES_KEY]:
                if sample_config[constants.SAMPLE_ID_KEY] == sample_id:
                    report_sample = sample(sample_config, log_level)
                    break
            if report_sample:
                self.sample = report_sample
            else:
                msg = "Could not find requested sample ID '%s' in config" % sample_id
                self.logger.error(msg)
                raise DjerbaReportError(msg)
        # populate the list of genetic alterations
        ga_factory = genetic_alteration_factory(log_level, log_path)
        ga_configs = config[constants.GENETIC_ALTERATIONS_KEY]
        self.alterations = [ # study_id is only required for cBioPortal, not Elba
            ga_factory.create_instance(conf, study_id=None) for conf in ga_configs
        ]

    def get_report_config(self, replace_null=True, require_consistent=True, overwrite=False):
        """
        Construct the reporting config data structure.
        Finds metric values at sample level and gene level.
        If 'require_consistent' is True: Check that each gene has the same attribute names
        If 'overwrite' is True: Replace any existing values for a metric with new ones
        """
        gene_metrics = {}
        for alteration in self.alterations:
            self.logger.debug("Processing genetic alteration: "+type(alteration).__name__)
            gene_metrics = alteration.update_gene_metrics(
                gene_metrics,
                self.sample_id,
                require_consistent,
                overwrite
            )
            self.logger.debug("Gene metrics after update: %s" % json.dumps(gene_metrics)[0:1000]+"...")
            self.sample.update_attributes(
                alteration.get_attributes_for_sample(self.sample_id),
                overwrite
            )
        # reorder gene-level metrics into a list
        gene_metrics_list = []
        for gene_id in gene_metrics.keys():
            # add an attribute for the gene name and append to list
            metrics = gene_metrics[gene_id]
            metrics[constants.GENE_KEY] = gene_id
            gene_metrics_list.append(metrics)
        self.logger.debug("Example gene metrics list entry: %s" % json.dumps(gene_metrics_list[0]))
        # assemble the config data structure
        config = {}
        config[constants.SAMPLE_INFO_KEY] = self.sample.get_attributes()
        config[constants.GENE_METRICS_KEY] = gene_metrics_list
        config[constants.REVIEW_STATUS_KEY] = -1 # placeholder; will be updated by Elba
        config[constants.SAMPLE_NAME_KEY] = self.sample.get_id()
        if replace_null:
            config = self.replace_null_with_string(config)
        self.validate(config)
        return config

    def replace_null_with_string(self, config):
        """Replace null/NaN values in config output with a string, eg. for easier processing in R"""
        for gene in config[constants.GENE_METRICS_KEY]:
            for key in gene.keys():
                if self.is_null(gene[key]):
                    gene[key] = self.NULL_STRING
        for key in config[constants.SAMPLE_INFO_KEY].keys():
            if self.is_null(config[constants.SAMPLE_INFO_KEY][key]):
                config[constants.SAMPLE_INFO_KEY][key] = self.NULL_STRING
        return config

    def write(self, config, out_path, force=False):
        """
        Write report config JSON to the given path, or stdout if the path is '-'.

        - If force is True, overwrite any existing output.
        - If replace_null is True, replace any None/NaN values with a standard string.
        """
        if out_path=='-':
            out_file = sys.stdout
        else:
            if os.path.exists(out_path):
                if force:
                    msg = "--force mode in effect; overwriting existing output %s" % out_path
                    self.logger.info(msg)
                else:
                    msg = "Output %s already exists; exiting. Use --force mode to overwrite." % out_path
                    self.logger.error(msg)
                    raise DjerbaReportError(msg)
            out_file = open(out_path, 'w')
        out_file.write(json.dumps(config, sort_keys=True, indent=4))
        if out_path!='-':
            out_file.close()

class DjerbaReportError(Exception):
    pass
