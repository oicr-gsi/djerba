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
    def UploadFile(self,json):
        print()
        print('upload file reached')
        print(json)
        print()
        return 
        self.logger.info('Database class Upload method STARTING')
        folder = folder
        config = configparser.ConfigParser()
        config.read("/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/couchdb.ini")              
        db = config["database"]["name"]
        base = config["database"]["base"]
        url = base + db
        dbs = base + '_all_dbs'
        time = datetime.now()
        dt_couchDB = time.strftime("%d/%m/%Y %H:%M") #time of file creation to db
        nextfolder = []
        nextfolder.append(folder)
        added = 0
        passed = []
        failed = []
        failed_code =[]
        failed_error = []
        while(len(nextfolder) != 0):
            currfolder = nextfolder[0]
            dir_content = (os.listdir(currfolder))  
            json_file = []
            for i in dir_content:
                n, ext = os.path.splitext(i)
                if ext == '.json':
                    type_json = (i, currfolder+'/'+i)
                    json_file.append(type_json)
                if ext == '':
                    nextfolder.append(currfolder+'/'+i)
            nextfolder.remove(nextfolder[0])

            if len(json_file) > 0:
                for file in json_file:
                    file_name = file[0]
                    file_path = file[1]
                    with open('{}'.format(file_path), 'r') as report:
                        data = json.load(report)
                        extracted_id = data["report"]["patient_info"]["Report ID"]
                        additional = {
                            '_id': '{}'.format(extracted_id), #DF val auto gen
                            'date_time': '{}'.format(dt_couchDB), 
                        }
                        upload = self.Merge(additional, data)
                        headers = {'Content-Type': 'application/json'}
                        submit = requests.post(url= url, headers= headers, json= upload)

                    status = submit.status_code
                    if status == 201:
                        added += 1
                        passed.append('Report ID: {}'.format(upload["_id"]))
                        self.logger.debug('Success uploading %s to %s database <status 201>', upload["_id"], db)
                    else:
                        json_string = submit.content.decode('utf-8') #convert bytes object 
                        py_dict = json.loads(json_string)
                        failed.append('Report ID: {}'.format(upload["_id"]))
                        failed_code.append('Status Code <{}>'.format(status))
                        failed_error.append('{}. {}'.format(py_dict["error"], py_dict["reason"]))
                        self.logger.debug('Error uploading %s to %s database for %s', upload["_id"], db, py_dict["reason"])
        
        '''FEEDBACK FOR DEBUGGING, COMMENT OUT LATER'''
        #if len(passed) !=0:
        #     print('Sucessful upload to {} database :)'.format(db), 'Status Code <201>', sep='\n')
        #     print()
            # for file in passed:
            #     print(file)
        # if len(passed) !=0 and len(failed) !=0: print()    
        # if len(failed) !=0:
        #     print('Error in {} database!'.format(db), '\n')
        #     for i in range(len(failed)):
        #         print(failed[i], failed_code[i], failed_error[i], sep='\n')
        # print()    
        # #if len(failed) !=0: print('Total files failed = {}'.format(len(failed)))
        # #if len(passed) !=0: print('Total files added = {}'.format(added))
        #print('Files Archived: {}/{}'.format(added, added + len(failed)))
        # print(folder)
        
        if len(passed) == 1: 
            #print('1 File Archived. {}'.format(passed[0]))
            self.logger.debug('1 File Archived. {}'.format(passed[0]))

        self.logger.info('Database class Upload method FINISHED')
        return status


    """ Searches for and uploads all json files within main and any sub folders """
    def UploadFolder(self,folder):
        self.logger.info('Database class Upload method STARTING')
        folder = folder
        config = configparser.ConfigParser()
        config.read("/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/couchdb.ini")              
        db = config["database"]["name"]
        base = config["database"]["base"]
        url = base + db
        dbs = base + '_all_dbs'
        time = datetime.now()
        dt_couchDB = time.strftime("%d/%m/%Y %H:%M") #time of file creation to db
        nextfolder = []
        nextfolder.append(folder)
        added = 0
        passed = []
        failed = []
        failed_code =[]
        failed_error = []
        while(len(nextfolder) != 0):
            currfolder = nextfolder[0]
            dir_content = (os.listdir(currfolder))  
            json_file = []
            for i in dir_content:
                n, ext = os.path.splitext(i)
                if ext == '.json':
                    type_json = (i, currfolder+'/'+i)
                    json_file.append(type_json)
                if ext == '':
                    nextfolder.append(currfolder+'/'+i)
            nextfolder.remove(nextfolder[0])

            if len(json_file) > 0:
                for file in json_file:
                    file_name = file[0]
                    file_path = file[1]
                    with open('{}'.format(file_path), 'r') as report:
                        data = json.load(report)
                        extracted_id = data["report"]["patient_info"]["Report ID"]
                        additional = {
                            '_id': '{}'.format(extracted_id), #DF val auto gen
                            'date_time': '{}'.format(dt_couchDB), 
                        }
                        upload = self.Merge(additional, data)
                        headers = {'Content-Type': 'application/json'}
                        submit = requests.post(url= url, headers= headers, json= upload)

                    status = submit.status_code
                    if status == 201:
                        added += 1
                        passed.append('Report ID: {}'.format(upload["_id"]))
                        self.logger.debug('Success uploading %s to %s database <status 201>', upload["_id"], db)
                    else:
                        json_string = submit.content.decode('utf-8') #convert bytes object 
                        py_dict = json.loads(json_string)
                        failed.append('Report ID: {}'.format(upload["_id"]))
                        failed_code.append('Status Code <{}>'.format(status))
                        failed_error.append('{}. {}'.format(py_dict["error"], py_dict["reason"]))
                        self.logger.debug('Error uploading %s to %s database for %s', upload["_id"], db, py_dict["reason"])
        
        '''FEEDBACK FOR DEBUGGING, COMMENT OUT LATER'''
        #if len(passed) !=0:
        #     print('Sucessful upload to {} database :)'.format(db), 'Status Code <201>', sep='\n')
        #     print()
            # for file in passed:
            #     print(file)
        # if len(passed) !=0 and len(failed) !=0: print()    
        # if len(failed) !=0:
        #     print('Error in {} database!'.format(db), '\n')
        #     for i in range(len(failed)):
        #         print(failed[i], failed_code[i], failed_error[i], sep='\n')
        # print()    
        # #if len(failed) !=0: print('Total files failed = {}'.format(len(failed)))
        # #if len(passed) !=0: print('Total files added = {}'.format(added))
        #print('Files Archived: {}/{}'.format(added, added + len(failed)))
        # print(folder)
        
        if len(passed) == 1: 
            #print('1 File Archived. {}'.format(passed[0]))
            self.logger.debug('1 File Archived. {}'.format(passed[0]))

        self.logger.info('Database class Upload method FINISHED')
        return status


