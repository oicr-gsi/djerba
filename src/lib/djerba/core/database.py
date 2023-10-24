"""Interface with a CouchDB instance for JSON report documents"""


import configparser
import json
import logging
import os
import requests
import string
import time
import djerba.core.constants as cc
import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from configparser import ConfigParser
from posixpath import join as posixjoin
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class database(logger):
    """Class to communicate with CouchDB via the API, eg. using HTTP GET/POST statements"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.debug("Initializing Djerba database object")

    def create_document(self, report_id, data):
        couch_info = {
            '_id': report_id,
            'last_updated': '{}'.format(self.timestamp()),
        }
        doc = {**couch_info, **data}
        return doc
    
    def get_upload_params(self, report_data):
        try:
            core_config = report_data[cc.CONFIG][cc.CORE]
            base = core_config[cc.ARCHIVE_URL]
            db = core_config[cc.ARCHIVE_NAME]
        except KeyError as err:
            msg = "Cannot read required upload param(s) from config: {0}".format(err)
            self.logger.error(msg)
            raise
        # read parameters from private dir
        private_dir = os.environ.get(cc.DJERBA_PRIVATE_DIR_VAR)
        if private_dir == None:
            msg = 'Environment variable {0}'.format(cc.DJERBA_PRIVATE_DIR_VAR)+\
                'is not configured; cannot find archive settings'
            self.logger.error(msg)
            raise RuntimeError(msg)
        config_path = os.path.join(private_dir, cc.ARCHIVE_CONFIG)
        path_validator(self.log_level, self.log_path).validate_input_file(config_path)
        config = ConfigParser()
        config.read(config_path)
        keys = [cc.USERNAME, cc.PASSWORD, cc.ADDRESS, cc.PORT]
        args = {key : config[cc.ARCHIVE_HEADER][key] for key in keys}
        base = string.Template(base).substitute(args)
        url = posixjoin(base, db)
        # find report ID from "core" (not to be confused with "config.core")
        report_id = report_data[cc.CORE][cc.REPORT_ID]
        return report_id, db, url

    def get_revision_and_url(self, report_id, url):
        url_id = posixjoin(url, report_id)
        result = requests.get(url_id)
        self.logger.debug("URL with ID: {0}".format(url_id)) ## TODO FIXME
        if result.status_code == 200:
            self.logger.debug('Successful HTTP GET for %s', report_id)
        else:
            self.logger.warning(
                'Failed HTTP GET for %s! Status Code <%s>',
                report_id,
                result.status_code
            )
            return None, url_id
        self.logger.debug("Result text: '{0}'".format(result.text))
        self.logger.debug("Result URL: '{0}'".format(result.url))
        self.logger.debug("Result status: '{0}'".format(result.status_code))
        self.logger.debug("Result headers: '{0}'".format(result.headers))
        rev = result.headers.get("ETag")
        self.logger.debug(f'Retrieved document _rev: {rev}')
        return rev, url_id

    def timestamp(self):
        return time.strftime("%d/%m/%Y_%H:%M:%SZ", time.gmtime())

    def update_document(self, report_id, rev, data):
        couch_info = {
            '_id': report_id,
            #'_rev': rev,
            'last_updated': self.timestamp(),
        }
        doc = {**couch_info, **data}
        return doc

    def upload_data(self, report_data):
        """
        Upload the report data structure to couchdb
        Full upload URL is intentionally not logged, as it contains the DB username/password
        """
        report_id, db, url = self.get_upload_params(report_data)
        headers = {'Content-Type': 'application/json'}
        attempts = 0
        http_post = True
        uploaded = False
        max_attempts = 5
        attempt = 0
        while uploaded == False and attempt < max_attempts:
            attempt +=1
            self.logger.debug("Uploading attempt {0} of {1}".format(attempt, max_attempts))
            if http_post == True:
                # create document
                self.logger.debug('Attempting POST for {0}'.format(report_id))
                upload_doc = self.create_document(report_id, report_data)
                result = requests.post(url=url, headers=headers, json=upload_doc)
            else:
                # update document
                rev, url_with_id = self.get_revision_and_url(report_id, url)
                if rev == None: self.logger.debug('Unable to get document _rev')
                updated_doc = self.update_document(report_id, rev, report_data)
                self.logger.debug('Attempting PUT for {0}'.format(report_id))
                self.logger.debug('URL to PUT: {0}'.format(url_with_id))
                self.logger.debug('rev to PUT: {0}'.format(rev))
                headers['If-Match'] = rev
                result = requests.put(url=url_with_id, headers=headers, json=updated_doc)
                self.logger.debug("Result text: '{0}'".format(result.text))
                self.logger.debug("Result URL: '{0}'".format(result.url))
                self.logger.debug("Result status: '{0}'".format(result.status_code))
                self.logger.debug("Result headers: '{0}'".format(result.headers))
            status = result.status_code
            if status == 201:
                uploaded = True
            elif status == 409:
                http_post = False
                self.logger.info('Document already exists, will retry with HTTP put request')
            else:
                self.logger.warning('Unexpected HTTP status <%s>, will retry', status)
            time.sleep(2)
        if uploaded == True:
            self.logger.info('Upload of "%s" to database "%s" successful.', report_id, db)
        else:
            self.logger.warning('Upload of "%s" to database "%s" FAILED', report_id, db)
        return uploaded, report_id

    def upload_file(self, json_path):
        """Read JSON from given path and upload to couchdb"""
        with open(json_path) as report:
            report_data = json.load(report)
        return self.upload_data(report_data)


    

