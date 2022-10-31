""" Searches for and uploads all json files within main and any sub folders """

import logging 
import configparser 
import requests
import json
import os
from urllib.parse import urljoin
from datetime import datetime

### change location of ini file below in AddFolder() !!!
""" Input from .ini includes ["database"]["name"] + ["database"]["url"] """

class Add():
    def __init__(self, level=logging.WARNING, filename=__name__):
        self.level = level
        self.filename = filename
        logging.basicConfig(level=level, format='%(asctime)s:%(filename)s:%(levelname)s: %(message)s')

    def CheckJSON(self, json_data):
        data = json_data
        noSection = False
        try: report_section = data["report"]
        except: 
            logger.warning('No report section in json')
            noSection = True 
        try: report_id = data["report"]["patient_info"]["Report ID"] 
        except: 
            logging.warning('No Report ID')
            report_id = None
            noSection = True
        try: author = data["report"]["author"]
        except: 
            logging.warning('No author')
            author = None
            noSection = True
        try: genomic_summary = data["report"]["genomic_summary"]
        except: 
            logging.warning('No genomic summary')
            genomic_summary = None
            hasSections = False
        notValid = False
        if noSection == False: 
            temp_author = author.casefold()
            if 'test' in temp_author: 
                logging.warning(f'{report_id} Author is Test Author')
                notValid = True
            temp_gensum = genomic_summary.casefold()
            if 'placeholder' in temp_gensum: 
                logging.warning(f'{report_id} Placeholder genomic_summary')
                notValid = True
        return report_id, notValid

    def CheckDuplicate(self, tuple_id_path):
        py_dict = {}
        duplicate = 0
        for i in range(len(tuple_id_path)):
            report_id = tuple_id_path[i][0]
            json_path = tuple_id_path[i][1]
            if report_id in py_dict:
                py_dict[report_id].append(json_path)
                duplicate += 1
            else:
                path_list = []
                path_list.append(json_path)
                py_dict[report_id] = path_list
        return py_dict, duplicate

    def AddFolder(self):
        config = configparser.ConfigParser()
        config.read("/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/archive/addfolder.ini") ### change location             
        db = config["database"]["name"]
        base = config["database"]["url"]
        folder = config["add"]["folder"]
        url = urljoin(base, db)
       
        nextfolder, passed, failed, failed_code, failed_error = ([] for i in range(5))
        nextfolder.append(folder)
        total, added = (0 for i in range(2))
        toUpload = []
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
                        report_id, notValid = self.CheckJSON(data)                    
                        total +=1
                        if notValid == False: toUpload.append((report_id, file_path))
        
        py_dict, duplicate = self.CheckDuplicate(toUpload)
        for key in py_dict:
            #print(key, py_dict[key])
            for i in range(len(py_dict[key])):
                #print(py_dict[key][i])
                with open(py_dict[key][i], 'r') as report:
                    data = json.load(report)
                    if i == 0: version_id = key
                    else: version_id = key+f'-db{i+1}'
                    #print(version_id)
                    time = datetime.now()
                    dt_couchDB = time.strftime("%d/%m/%Y %H:%M") #time of file creation to db
                    additional = {
                        '_id': '{}'.format(version_id), #DF val auto gen
                        'last_updated': '{}'.format(dt_couchDB), 
                    }
                    upload = {**additional, **data}
                    headers = {'Content-Type': 'application/json'}
                    submit = requests.post(url= url, headers= headers, json= upload)

                    status = submit.status_code
                    if status == 201:
                        added += 1
                        passed.append('Report ID: {}'.format(version_id))
                        logging.info('%s database. %s Uploaded %s', db, status,version_id)
                    else:
                        json_string = submit.content.decode('utf-8') #convert bytes object 
                        pydict = json.loads(json_string)
                        failed_code.append('Status Code <{}>'.format(status))
                        failed_error.append('{}. {}'.format(pydict["error"], pydict["reason"]))
                        failed.append('Report ID: {}'.format(version_id))
                        logging.error('%s database. %s %s %s', db, status, pydict["reason"], version_id)
        
        ##EXPANDED TERMINAL FEEDBACK
        # if len(passed) !=0:
        #     print(f'Sucessful upload to {db} database :)')
        #     print()
        #     for file in passed:
        #         print(file)
        # if len(passed) !=0 and len(failed) !=0: print()    
        # if len(failed) !=0:
        #     print(f'Error uploading to {db} database!', '\n')
        #     for i in range(len(failed)):
        #         print(failed[i], failed_code[i], failed_error[i])
        
        print(f'Total jsons found: {total}.  Valid to upload: {len(toUpload)}/{total}.  Duplicate report id: {duplicate}')
        print()    
        print('Files Archived: {}/{}'.format(added, added + len(failed)))
        print(folder)
        return
        # return status 
    
if __name__ == '__main__':
    Add().AddFolder()

