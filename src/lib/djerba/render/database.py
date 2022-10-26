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
from urllib.parse import urljoin
from djerba.util.logger import logger

class database(logger):
    """Class to communicate with CouchDB via the API, eg. using HTTP GET/POST statements"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Initializing Djerba database object")
    
    def Merge(self,dict1,dict2):
        combined = {**dict1, **dict2}
        return combined

    """ Upload json to couchdb"""
    def upload_file(self, json_path):
        time = datetime.now()
        dt_couchDB = time.strftime("%d/%m/%Y %H:%M") 

        with open(json_path) as report:
            data = json.load(report)
            config = data.get(constants.SUPPLEMENTARY).get(constants.CONFIG)
            base = config[ini.SETTINGS][ini.ARCHIVE_URL]
            db = config[ini.SETTINGS][ini.ARCHIVE_NAME]           
            url = urljoin(base, db)
            report_id = data["report"]["patient_info"]["Report ID"]
            couch_info = {
                '_id': '{}'.format(report_id), #DF val auto gen
                'last_updated': '{}'.format(dt_couchDB),
            }
            upload = self.Merge(couch_info, data)
            headers = {'Content-Type': 'application/json'}
            submit = requests.post(url= url, headers= headers, json= upload)
        
        attempt = 0
        status = submit.status_code
        uploaded = False
        while uploaded == False and attempt < 5:
            if status == 201:
                self.logger.info('Success uploading %s to %s database <status 201>', upload["_id"], db)
                uploaded = True 
            elif status == 409:
                json_string = submit.content.decode('utf-8') #convert bytes object 
                py_dict = json.loads(json_string)
                self.logger.debug(f'Error uploading {report_id} Status Code <409> {py_dict["error"]} {py_dict["reason"]}')
                url_id = url + f'/{report_id}'
                pull = requests.get(url_id)
                pull = json.loads(pull.text)
                self.logger.info(f'_rev: {pull["_rev"]}')
                rev = {
                    '_id': '{}'.format(report_id), 
                    '_rev': f'{pull["_rev"]}',
                    'last_updated': '{}'.format(dt_couchDB),
                }
                upload = self.Merge(rev, data)
                sleep(2) 
                submit = requests.put(url=url_id, headers= headers, json=upload)   
                status = submit.status_code 
                attempt += 1 
            else:
                self.logger.warning(f'HTTP code: {status}')   
                attempt += 1    
    
        if uploaded == False and attempt == 5: self.logger.warning('HTTP Request Timed Out')
        if status == 201: self.logger.info('File Archived: {}'.format(upload["_id"]))
        return status, report_id

