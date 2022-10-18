
import logging #change path below for test.log
#from djerba.util.logger import logger
from logger import logger
from datetime import datetime

# time = datetime.now()
# dt_log = time.strftime("%d%m%Y_%H%M")

# log_path = '/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/lauren/logpath/'
# log_name = 'test' #+f'_{dt_log}'
# logging.basicConfig(format='%(levelname)s:%(message)s', filename=log_path+log_name+'.log', encoding='utf-8', level=logging.DEBUG)

# logging.info('addclasslog.py imported <first line>')

import configparser 
import requests
import json
import os

'''
Input from info.ini includes ["database"]["name"] + ["database"]["base"] + ["add"]["folder"] 
Searches for and uploads all json files within main folder and any subfolders 
'''

class Add(logger):
    def __init__(self, log_level=logging.DEBUG, log_path = '/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/test.log'):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info('Initializing Add object from addclasslog.py')

    def Merge(self,dict1,dict2):
        combined = {**dict1, **dict2}
        return combined

    def AddFolder(self, folder):
        self.logger.info('AddFolder method STARTED from addclasslog.py')
        config = configparser.ConfigParser()
        config.read("/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/info.ini")              
        #folder = config["add"]["folder"]
        folder = folder
        db = config["database"]["name"]
        base = config["database"]["base"]
        url = base + db
        dbs = base + '_all_dbs'
        time = datetime.now()
        dt_couchDB = time.strftime("%d/%m/%Y %H:%M") #time of file creation

        nextfolder = []
        nextfolder.append(folder)
        added = 0
        passed = []
        failed = []
        failed_code =[]
        failed_error = []
        
        while(len(nextfolder) != 0):
            currfolder = nextfolder[0]
            #print(currfolder)
            dir_content = (os.listdir(currfolder))  
            json_file = []
            #print(nextfolder)
            for i in dir_content:
                n, ext = os.path.splitext(i)
                if ext == '.json':
                    type_json = (i, currfolder+'/'+i)
                    json_file.append(type_json)
                if ext == '':
                    nextfolder.append(currfolder+'/'+i)
            nextfolder.remove(nextfolder[0])
            #print(json_file)
            #print(nextfolder)
            #print()

            if len(json_file) > 0:
                for file in json_file:
                    file_name = file[0]
                    file_path = file[1]

                    with open('{}'.format(file_path), 'r') as report:
                        data = json.load(report)
                        extracted_id = data["report"]["patient_info"]["Report ID"]
                        additional = {
                            '_id': '{}'.format(extracted_id), #df val auto gen
                            'datetime': '{}'.format(dt_couchDB), 
                            
                            #fields from report for Table filter in dropdown order - example fields below
                            'clinically relevant variants': '{}'.format(data["report"]["oncogenic_somatic_CNVs"]["Clinically relevant variants"]), 
                            'total variants': '{}'.format(data["report"]["oncogenic_somatic_CNVs"]["Total variants"]), 
                            'primary cancer': '{}'.format(data["report"]["patient_info"]["Primary cancer"]), 
                            'mean coverage': '{}'.format(data["supplementary"]["config"]["inputs"]["mean_coverage"]), 
                            'genomic summary': '{}'.format(data["report"]["genomic_summary"]), 
                            'sex': '{}'.format(data["report"]["patient_info"]["Genetic Sex"]), 
                            'author': '{}'.format(data["report"]["author"]), 
                            'failed': '{}'.format(data["report"]["failed"]), 
                            ###
                            'note': '', #extra optional information added between Djerba and CouchDB stage
                        }
                        upload = self.Merge(additional, data)
                        headers = {'Content-Type': 'application/json'}
                        submit = requests.post(url= url, headers= headers, json= upload)

                    status = submit.status_code
                    if status == 201:
                        added += 1
                        passed.append('Report ID: {}'.format(upload["_id"]))
                        self.logger.info('Success uploading %s to %s database <status 201>', upload["_id"], db)
                    else:
                        json_string = submit.content.decode('utf-8') #convert bytes object 
                        py_dict = json.loads(json_string)
                        failed.append('Report ID: {}'.format(upload["_id"]))
                        failed_code.append('Status Code <{}>'.format(status))
                        failed_error.append('{}. {}'.format(py_dict["error"], py_dict["reason"]))
                        self.logger.error('Error uploading %s to %s database for %s', upload["_id"], db, py_dict["reason"])

        if len(passed) !=0:
            print('Sucessful upload to {} database :)'.format(db), 'Status Code <201>', sep='\n')
            print()
            for file in passed:
                print(file)
        if len(passed) !=0 and len(failed) !=0: print()    
        if len(failed) !=0:
            print('Error in {} database!'.format(db), '\n')
            for i in range(len(failed)):
                print(failed[i], failed_code[i], failed_error[i], sep='\n')
        print()    
        #if len(failed) !=0: print('Total files failed = {}'.format(len(failed)))
        #if len(passed) !=0: print('Total files added = {}'.format(added))
        print('Files Added: {}/{}'.format(added, added + len(failed)))
        print(folder)  #remove if only want return stored below...
        self.logger.info('AddFolder method FINISHED from addclasslog.py')
        return folder  #output when assign to variable then print it

# a = Add()
# a.AddFolder()


