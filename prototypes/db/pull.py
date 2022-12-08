import logging
import requests
import json
import csv
import os 
import posixpath
import pandas as pd
from datetime import datetime
from tabulate import tabulate

class Pull():
    ''' change location of database here with db and base, when called in design.py inherits values from there'''
    def __init__(self, db='djerba', base='http://admin:djerba123@10.30.133.78:5984/', level=logging.INFO, log_path=None, filename=__name__):
    #def __init__(self, db='test', base='http://admin:cgi@127.0.0.1:5984/', level=logging.INFO, log_path=None, filename=__name__):
        self.db = db
        self.base = base
        self.url = posixpath.join(self.base,self.db)          
        self.level = level
        self.filename = filename
        self.log_path = log_path
        if log_path != None:
            file_path = join(self.log_path, self.filename)
            file_path += '.log'
        else: file_path = None
        logging.basicConfig(level=level, filename=file_path, format=f'%(asctime)s:%(filename)s:%(levelname)s: %(message)s', datefmt='%Y-%m-%d_%H:%M:%S')

    def AddPlaceholderKeysForEachID(self, qtype, new_list, views=None, headers=None):
        '''create query key placeholders for each unique report id dictionary'''
        if qtype == 'm':
            for view in views:
                if view != '_id': #from view name
                    for entry in new_list:
                        py_dict = entry
                        py_dict[view] = None
        elif qtype == 'e' or qtype == 'l' or qtype =='g': 
            for entry in new_list:
                for header in headers:
                    if header != '_id': #from view name
                        py_dict = entry
                        py_dict[header] = None
        return new_list

    def AddValuesForKeys(self, qtype, new_list, files, view_equal=None, view=None):
        '''assign value to key for each unique report id'''
        for file in files:
            py_dict = file
            report_id = py_dict["id"] #_id online
            key = py_dict["key"]
            value = py_dict["value"]
            for entry in new_list:
                new_dict = entry
                if report_id == new_dict["_id"] and key != '_id':
                    if qtype == 'm': new_dict[key] = value
                    elif qtype == 'e' or qtype == 'l' or qtype == 'g':
                        if key == 'bool': new_dict[view_equal] = value
                        else: new_dict[view] = value
        return new_list

    def CheckAndSwitchForwardSlashOrPlus(self, string_to_search, url=False):
        '''for field in json such as Site in biopsy/surgery to account for conflicts with '/' in splitting query as
        nested keys accessed by forward slash in query and also error w/ HTTP requests in url'''
        if url == False:
            if 'Site of biopsy/surgery' in string_to_search:
                string_to_search = string_to_search.replace('Site of biopsy/surgery', 'Site of biopsy+surgery')
            elif 'Site of biopsy+surgery' in string_to_search:
                string_to_search = string_to_search.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
        elif url == True:
            if 'Site of biopsy/surgery' in string_to_search:
                string_to_search = string_to_search.replace('Site of biopsy/surgery', 'Site of biopsy%2Fsurgery')
            elif 'Site of biopsy%2Fsurgery' in string_to_search: 
                string_to_search = string_to_search.replace('Site of biopsy%2Fsurgery', 'Site of biopsy/surgery')
        return string_to_search

    def CreateEmptyArrayWithUniqueIDDictionaries(self, files):
        '''consolidates duplicate report id's which is expected if query on more than one field'''
        new_list = []
        for file in files:
            curr_dict = file
            new_dict = {}
            new_dict["_id"] = curr_dict["id"] #_id online 
            if file == files[0]: 
                new_list.append(new_dict)
            else:
                exists = []
                for i in new_list: exists.append(i["_id"])
                if exists.count(curr_dict["id"]) == 0:
                    new_list.append(new_dict)
        return new_list

    def DatabaseStat(self): 
        '''check database exists and number of documents'''
        head = requests.get(self.url)
        if head.status_code == 200: 
            logging.info('<Response [200]> Ok Get Request')
            py_dict = json.loads(head.text)
            total_doc = py_dict["doc_count"]
            del_doc = py_dict["doc_del_count"]
            url = self.url.split("/")
            db = url[-1]
            stats = f'{self.db.capitalize()} Database. Total Doc (including design etc.) = {total_doc}. Deleted Doc = {del_doc}'            
            logging.debug(str(stats))
            return self.db, total_doc, del_doc
        elif head.status_code == 404: logging.error('<Response [404]> Not Found. Database does not exist')
        else:
            status_str = str(head)+str(head.content)
            logging.error(status_str)
        return 

    def DeleteDesignDoc(self, design_doc_name):
        '''deletes design document from database'''
        try: doc, _id, _rev = self.DesignDocExistance(design_doc_name)
        except: return False
        url_id = posixpath.join(self.url, _id)
        rm = requests.delete(url_id+'?rev='+_rev)
        if rm.status_code == 200: 
            logging.info('<Response [200]> Delete Ok')
            return True
        else:
            status_str = str(rm)+str(rm.content)
            logging.error(status_str)
            return False
        
    def DesignDocExistance(self, design_doc_name): 
        '''checks if design document already exists on database '''
        design = requests.get('{}/_design/{}'.format(self.url, design_doc_name))
        if design.status_code == 200: 
            logging.info('<Response [200]> Design Document Found Ok')
            doc = json.loads(design.text) #convert json str to py dict
            _id = doc["_id"]
            _rev = doc["_rev"]
            return doc, _id, _rev
        elif design.status_code == 404: 
            logging.error(f'<Response [404]> Not Found. Document Missing "{design_doc_name}" from {self.db} database')
        else:
            status_str = str(design)+str(design.content)
            logging.error(status_str)
        return 

    def Filter(self, qtype, files, view, datatype=None):
        '''pre-processing to convert raw json from db query into terminal/csv table format or json'''
        files = files
        if qtype == 'm': views = view.split("&")
        else:
            view_equal = view
            if qtype == 'e': view, equal = view.split("=")   
            elif qtype == 'l': view, equal = view.split("<")   
            elif qtype == 'g': view, equal = view.split(">")
            headers = [view, view_equal]

        new_list = self.CreateEmptyArrayWithUniqueIDDictionaries(files)
        
        if qtype == 'm':
            new_list = self.AddPlaceholderKeysForEachID(qtype, new_list, views=views)
            new_list = self.AddValuesForKeys(qtype, new_list, files)
            return new_list
        else:
            new_list = self.AddPlaceholderKeysForEachID(qtype, new_list, headers=headers)
            new_list = self.AddValuesForKeys(qtype, new_list, files, view_equal, view)
            true_list, equal, number = self.OnlyQueryMatches(files, view_equal, new_list)
            return new_list, true_list, equal, number
        return

    def OnlyQueryMatches(self, files, view_equal, new_list):
        '''displays all files not just those that match operator for equal, less, or great'''
        true_list = []
        equal=0
        for query in new_list:
            check_dict = query
            if check_dict[f"{view_equal}"] == True:
                true_list.append(query)
                equal += 1
        number = int(len(files)/2) #b/c query for key and bool comparison so document appears twice
        return true_list, equal, number

    def OutCSV(self, design_doc_name, view, files, out_dir):
        '''save query results as csv'''
        view = self.CheckAndSwitchForwardSlashOrPlus(view)
        out_name_doc = self.OutNameClean(design_doc_name)
        out_name_view = self.OutNameClean(view)
        out_name = f'{out_name_doc}_{out_name_view}'
        out_path = f'{posixpath.join(out_dir, out_name)}.csv'
        csv_file = open(out_path, 'w')
        writer = csv.writer(csv_file)
        count = 0
        for line in files:
            if count == 0:
                header = list(line.keys()) 
                writer.writerow(header)
                count +=1
            writer.writerow(line.values())
        csv_file.close()
        return out_path

    def OutDir(self):
        '''creates output directory in same location as these files'''
        run_path = os.path.realpath(__file__) 
        base = run_path.split("/")
        base = base[:-1]
        base = "/".join(base)
        if os.path.exists(posixpath.join(base, 'extract')) == False:
            os.mkdir(posixpath.join(base, 'extract'))
        out_dir = posixpath.join(base, 'extract')
        return out_dir

    def OutJSON(self, design_doc_name, view, files, out_dir): 
        '''save query results as json, note entire json is contained within a list'''
        view = self.CheckAndSwitchForwardSlashOrPlus(view)
        out_name_doc = self.OutNameClean(design_doc_name)
        out_name_view = self.OutNameClean(view)
        out_name = f'{out_name_doc}_{out_name_view}'
        out_path = f'{posixpath.join(out_dir,out_name)}.json'
        json_str = json.dumps(files, indent= 4)
        with open(out_path, 'w') as outfile:
            outfile.write(json_str)
        return out_path

    def OutNameClean(self, out_name):
        '''remove special characters and spaces from string for cleaner output file name'''
        out_name = out_name.replace(" ", "")
        out_name = out_name.replace("&", "") 
        out_name = out_name.replace("=", "") 
        out_name = out_name.replace("<", "") 
        out_name = out_name.replace(">", "") 
        out_name = out_name.replace("+", "") 
        #within keys
        out_name = out_name.replace(" ", "")
        out_name = out_name.replace("_", "")
        out_name = out_name.replace("(", "") 
        out_name = out_name.replace(")", "") 
        out_name = out_name.replace("/", "") 
        out_name = out_name.replace("%", "") 
        return out_name

    def TerminalPrint(self,search, number, files, view, equal=None):
        '''display results in terminal (csv format), turned on with -p flag'''
        if len(search) > 0: print() #break before views for cleanliness 
        time = datetime.now()
        time = time.strftime("%d/%m/%Y %H:%M") #time of file creation to db
        if equal == None: print(f'{number} Files Found', time, f'<{view}>')
        else: print(f'{equal}/{number} Files Found', time, f'<{view}>')
        #for file in files: print(file) #condensed raw terminal view       
        df = pd.DataFrame(files)
        df.index = df.index + 1
        header = list(files[0].keys())
        header.insert(0, '#')
        print(tabulate(df, headers=header, showindex=True))
        return

    def Query(self, url, design_doc_name, search, out_args, eq_all, qtype, datatype=None):
        '''main function to pull query off database and print/save results'''
        count = 0
        for view in search:
            view = self.CheckAndSwitchForwardSlashOrPlus(view, url=True)
            pull = requests.get('{}/_design/{}/_view/{}'.format(url, design_doc_name, view))
            view = self.CheckAndSwitchForwardSlashOrPlus(view, url=True)

            py_dict = json.loads(pull.text)
            try: number = py_dict["total_rows"]
            except:
                logging.error('Query does not match design doc view. Consider deleting design document or matching query.')
                return

            files = py_dict["rows"] #array of jsons
            if qtype == 'm':
                files = self.Filter(qtype, files, view)
                number = len(files)
            if qtype == 'e' or qtype == 'l' or qtype == 'g':
                if datatype == None: logging.warning('datatype argument not passed')
                else:
                    new_list, true_list, equal, number = self.Filter(qtype, files, view, datatype=datatype[count])
                    if eq_all == True: files = new_list
                    else: files = true_list
                    count += 1

            #out_args = [args.cmdprint, args.outcsv, args.outjson, args.outdir]
            if qtype == 'e' or qtype == 'l' or qtype== 'g':
                if out_args[0] == True: self.TerminalPrint(search, number, files, view, equal)
            else:
                if out_args[0] == True: self.TerminalPrint(search, number, files, view)
            if out_args[1] == True or out_args[2] == True:
                if out_args[3] == None: out_dir = self.OutDir()
                else: out_dir = out_args[3]
                if out_args[1] == True: 
                    outpathcsv = self.OutCSV(design_doc_name, view, files, out_dir)
                    logging.debug(f"csv path: {outpathcsv}")
                if out_args[2] == True: 
                    outpathjson = self.OutJSON(design_doc_name, view, files, out_dir)
                    logging.debug(f"json path: {outpathjson}")
        return 

if __name__ == "__main__":
    logging.error('this script pull.py is called by design.py') 





