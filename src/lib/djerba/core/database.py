"""Interface with a CouchDB instance for JSON report documents"""


import configparser
import json
import logging
import os
import requests
import time
import djerba.core.constants as core_constants
import djerba.util.constants as constants
import djerba.util.ini_fields as ini

from urllib.parse import urljoin
from djerba.util.logger import logger

class database(logger):
    """Class to communicate with CouchDB via the API, eg. using HTTP GET/POST statements"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.debug("Initializing Djerba database object")

    def combine_dictionaries(self, dict1, dict2):
        comb = {**dict1, **dict2}
        return comb

    def create_document(self, report_id):
        couch_info = {
            '_id': report_id,
            'last_updated': '{}'.format(self.date_time()),
        }
        return couch_info

    def date_time(self):
        "added last_updated date and time"
        last_updated = time.strftime("%d/%m/%Y %H:%M")
        return last_updated

    def get_upload_params(self, report_data):
        # TODO read password from private dir
        try:
            core_config = report_data[core_constants.CONFIG][core_constants.CORE]
            base = core_config[core_constants.ARCHIVE_URL]
            db = core_config[core_constants.ARCHIVE_NAME]
        except KeyError as err:
            msg = "Cannot read required upload param(s) from config: {0}".format(err)
            self.logger.error(msg)
            raise
        url = urljoin(base, db)
        # find report ID from "core" (not to be confused with "config.core")
        report_id = report_data[core_constants.CORE][core_constants.REPORT_ID]
        return report_id, base, db, url

    def get_revision_and_url(self, report_id, url):
        url_id = urljoin(url, report_id)
        result = requests.get(url_id)
        if result.status_code == 200:
            self.logger.debug('Successful HTTP Pull Request from %s', url_id)
        else:
            self.logger.debug('Error with HTTP Pull at %s! Status Code <%s>', url_id, result.status_code)
            return None, url_id
        rev = json.loads(pull.text).get("_rev")
        self.logger.debug(f'Retrieved document _rev: {rev}')
        return rev, url_id

    def update_document(self, report_id, rev):
        couch_info = {
            '_id': report_id,
            '_rev': rev,
            'last_updated': time.strftime("%Y-%m-%d_%H:%M:%S"),
        }
        return couch_info

    def upload_data(self, report_data):
        """ Upload the report data structure to couchdb"""
        report_id, base, db, url = self.get_upload_params(report_data)
        couch_info = self.create_document(report_id)
        upload = self.combine_dictionaries(couch_info, report_data)
        headers = {'Content-Type': 'application/json'}
        attempts = 0
        http_post = True
        uploaded = False
        while uploaded == False and attempts <5:
            if http_post == True: #create document
                submit = requests.post(url= url, headers= headers, json=upload)
                self.logger.debug('Creating document in database')
            else: #update document
                rev, url_id = self.get_revision_and_url(report_id, url)
                if rev == None: self.logger.debug('Unable to get document _rev')
                couch_info = self.update_document(report_id, rev)
                upload = self.combine_dictionaries(couch_info, report_data)
                submit = requests.put(url=url_id, headers= headers, json=upload)
                self.logger.debug('Updating document in database')
            status = submit.status_code
            if status == 201: uploaded = True
            elif status == 409:
                http_post = False
                self.logger.info('Document already exists, will retry with HTTP put request')
            else:
                self.logger.warning('Error! Unknown HTTP Status Code <%s>, will retry', status)
            time.sleep(2)
            attempts +=1
        if uploaded == True:
            self.logger.info('Upload successful to DB "%s". File archived: %s', db, report_id)
        else:
            self.logger.warning('Upload of "%s" to DB "%s" failed', report_id, db)
        return uploaded, report_id

    def upload_file(self, json_path):
        """Read JSON from given path and upload to couchdb"""
        with open(json_path) as report:
            report_data = json.load(report)
        return self.upload_data(report_data)


    

