"""Interface with a CouchDB instance for JSON report documents"""

import logging
import configparser
import requests
import json
import os

import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from time import sleep
from datetime import datetime
from posixpath import join
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
            '_id': '{}'.format(report_id), 
            'last_updated': '{}'.format(self.date_time()),
        }
        return couch_info

    def date_time(self):
        "added last_updated date and time"
        time = datetime.now()
        last_updated = time.strftime("%d/%m/%Y %H:%M")
        return last_updated

    def get_upload_params(self, report_data):
        config = report_data.get(constants.SUPPLEMENTARY).get(constants.CONFIG)
        base = config[ini.SETTINGS][ini.ARCHIVE_URL]
        db = config[ini.SETTINGS][ini.ARCHIVE_NAME]
        url = join(base, db)
        report_id = report_data["report"]["patient_info"]["Report ID"]
        return report_id, base, db, url

    def get_revision_and_url(self, report_id, url):
        url_id = join(url, report_id)
        pull = requests.get(url_id)
        if pull.status_code == 200:
            self.logger.debug('Successful HTTP Pull Request from %s', url_id)
        else:
            self.logger.debug('Error with HTTP Pull at %s! Status Code <%s>', url_id, pull.status_code)
            return None, url_id
        pull = json.loads(pull.text)
        rev = pull["_rev"]
        self.logger.debug(f'Retrieved document _rev: {rev}')
        return rev, url_id

    def update_document(self, report_id, rev):
        couch_info = {
            '_id': '{}'.format(report_id),
            '_rev': '{}'.format(rev),
            'last_updated': '{}'.format(self.date_time()),
        }
        return couch_info

    def upload_file(self, json_path):
        """ Upload json to couchdb"""
        with open(json_path) as report:
            report_data = json.load(report)
            report.close()

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
            sleep(2)
            attempts +=1

        if uploaded == True:
            self.logger.info('Upload succesful to %s. File archived: %s', db, report_id)
        else:
            self.logger.warning('Upload of %s to %s database failed', report_id, db)
        return uploaded, report_id



    

