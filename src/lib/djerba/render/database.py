"""Interface with a CouchDB instance for JSON report documents"""

""" Input from couchdb.ini includes ["database"]["name"] + ["database"]["base"] """

import logging 
import configparser 
import requests
import json
import os

from datetime import datetime
from djerba.util.logger import logger
#from djerba.render.addclasslog import Add 

class Database(logger):
    """Class to communicate with CouchDB via the API, eg. using HTTP GET/POST statements"""

    def __init__(self, log_level=logging.WARN, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Initializing Djerba database object")
    
    def Merge(self,dict1,dict2):
        combined = {**dict1, **dict2}
        return combined

    """ Upload json to db"""
    def UploadFile(self,json_path):
        self.logger.info('UploadFile method from database.py STARTING')
        config = configparser.ConfigParser()
        config.read("/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/couchdb.ini")              
        db = config["database"]["name"]
        base = config["database"]["base"]
        url = base + db
        time = datetime.now()
        dt_couchDB = time.strftime("%d/%m/%Y %H:%M") #time of file creation to db

        with open(json_path) as report:
            data = json.load(report)
            report_id = data["report"]["patient_info"]["Report ID"]
            couch_info = {
                '_id': '{}'.format(report_id), #DF val auto gen
                'date_time': '{}'.format(dt_couchDB), 
            }
            upload = self.Merge(couch_info, data)
            headers = {'Content-Type': 'application/json'}
            submit = requests.post(url= url, headers= headers, json= upload)
        
        status = submit.status_code
        uploaded = False
        while uploaded == False:
            if status == 201:
                #print('Sucessful upload of Report ID: {} to {} database :)'.format(upload["_id"],db), 'Status Code <201>')
                self.logger.debug('Success uploading %s to %s database <status 201>', upload["_id"], db)
                uploaded = True 
            elif status == 409:
                json_string = submit.content.decode('utf-8') #convert bytes object 
                py_dict = json.loads(json_string)
                self.logger.debug(f'Error uploading {upload["_id"]} Status Code <409> {py_dict["error"]} {py_dict["reason"]}')
                url_id = url + f'/{upload["_id"]}'
                pull = requests.get(url_id)
                pull = json.loads(pull.text)                
                rev = {
                    '_id': '{}'.format(report_id), #DF val auto gen
                    '_rev': f'{pull["_rev"]}',
                    'date_time': '{}'.format(dt_couchDB), 
                }
                upload = self.Merge(rev, data)
                submit = requests.put(url=url_id, headers= headers, json=upload)   
                status = submit.status_code         
                        
        print('File Archived: {}'.format(upload["_id"]))
        self.logger.info('File Archived: {}'.format(upload["_id"]))
        self.logger.info('Database class Upload method FINISHED')
        return status
