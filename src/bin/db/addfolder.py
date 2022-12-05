""" Searches for and uploads djerba_report json files in main and sub folders"""
import argparse 
import logging 
import requests
import json
import os
from posixpath import join
from datetime import datetime

class Add():
    def __init__(self, level=logging.WARNING, filename=__name__):
        self.level = level
        self.filename = filename
        logging.basicConfig(level=level, format=f'%(asctime)s:%(filename)s:%(levelname)s: %(message)s', datefmt='%Y-%m-%d_%H:%M:%S')

    def CheckJSON(self, json_data):
        data = json_data
        noSection = False
        try: report_section = data["report"]
        except: 
            logging.warning('No report section in json')
            noSection = True 
        try: report_id = data["report"]["patient_info"]["Report ID"] #REPORT ID is used as file name in couchdb 
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
        #check for and group reports with same report_id
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

    def AddFolder(self, folder, db_args, cmdprint):
        db = db_args[0]
        base = db_args[1]
        folder = folder
        url = join(base, db)
        
        nextfolder, passed, failed, failed_code, failed_error = ([] for i in range(5))
        nextfolder.append(folder)
        total, added = (0 for i in range(2))
        toUpload = []
        #recursively search for json file according to condition below
        while(len(nextfolder) != 0):
            currfolder = nextfolder[0]
            dir_content = (os.listdir(currfolder)) 
            json_file = []
            for i in dir_content:
                n, ext = os.path.splitext(i)
                #condition for upload - change accordingly (ie. below for folder  /.mounts/labs/CGI/cap-djerba) 
                if ext == '.json' and 'djerba_report' in n and currfolder.endswith('archive'): 
                    type_json = (i, currfolder+'/'+i)
                    json_file.append(type_json)
                if os.path.isdir(currfolder+'/'+i) == True:
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
            for i in range(len(py_dict[key])):
                with open(py_dict[key][i], 'r') as report:
                    data = json.load(report)
                    #if multiple 'valid' jsons of same report_id, upload all w versioning suffix in case
                    if i == 0: version_id = key
                    else: version_id = key+f'-db{i+1}'
                    time = datetime.now()
                    dt_couchDB = time.strftime("%d/%m/%Y %H:%M") #time of file creation to db
                    additional = {
                        '_id': '{}'.format(version_id), #NAME OF FILE IN COUCH DB
                        'last_updated': '{}'.format(dt_couchDB), 
                    }
                    upload = {**additional, **data}
                    headers = {'Content-Type': 'application/json'}
                    logging.info(f'uploading to db: {url}')
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
        
        if cmdprint == True:
            if len(passed) !=0:
                print(f'Sucessful upload to {db} database :)')
                print()
                for file in passed:
                    print(file)
            if len(passed) !=0 and len(failed) !=0: print()    
            if len(failed) !=0:
                print(f'Error uploading to {db} database!', '\n')
                for i in range(len(failed)):
                    print(failed[i], failed_code[i], failed_error[i])
        else:
            for f in passed: print(f)
            
        print(f'Total jsons found: {total}.  Valid to upload: {len(toUpload)}/{total}.  Duplicate report id: {duplicate}','\n')   
        print('Files Archived: {}/{}'.format(added, added + len(failed)), folder, sep='\n')
        return

    def SetUp(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('folder', help='path of DIR to upload') #, type=str, action="store", dest="folder")
        parser.add_argument("-n", "--name", help="database name, default is djerba_test", action="store", type=str, dest="name", default=None)
        parser.add_argument("-u", "--url", help="base url, default is http://admin:djerba123@10.30.133.78:5984/", action="store", type=str, dest="url", default=None)
        parser.add_argument("-p", "--print", help="expanded print to terminal, default is false", action="store_true", dest="cmdprint", default=False)
        args = parser.parse_args()
        folder = args.folder
        cmdprint = args.cmdprint
        db_args = [args.name, args.url]        
        if os.path.exists(folder) == False: 
            logging.error("path doesn't exist")
            return
        if os.path.isdir(folder) == False:
            logging.error("path isn't a directory")
            return
        if args.name == None:
            db_args[0] = 'djerba_test' 
            logging.warning('no input db name, default to "djerba_test"')
        if args.url == None: 
            db_args[1] = "http://admin:djerba123@10.30.133.78:5984/"
            logging.warning('no input db url, default to "http://admin:djerba123@10.30.133.78:5984/"')
        if args.name != None or args.url != None:
            check_db = requests.get(join(args.url,args.name))
            if check_db.status_code != 200: 
                logging.warning('error with database name and/or url')
                return
        self.AddFolder(folder, db_args, cmdprint)
        return

if __name__ == '__main__':
    Add().SetUp()


