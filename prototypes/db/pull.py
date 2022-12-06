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

    def DBStat(self): 
        head = requests.get(self.url)
        if head.status_code == 200: 
            logging.info('<Response [200]> Ok')
            py_dict = json.loads(head.text)
            total_doc = py_dict["doc_count"]
            del_doc = py_dict["doc_del_count"]
            url = self.url.split("/")
            db = url[-1]
            stats = f'{self.db.capitalize()} Database. Total Doc = {total_doc}. Deleted Doc = {del_doc}'            
            logging.debug(str(stats))
            return self.db, total_doc, del_doc
        elif head.status_code == 404: logging.error('<Response [404]> Not Found. Database does not exist')
        else:
            status_str = str(head)+str(head.content)
            logging.error(status_str)
        return 

    def DesignDoc(self, design_doc_name): 
        design = requests.get('{}/_design/{}'.format(self.url, design_doc_name))
        if design.status_code == 200: 
            logging.info('<Response [200]> Found Ok')
            doc = json.loads(design.text) #convert json str to py dict
            _id = doc["_id"]
            _rev = doc["_rev"]
            return doc, _id, _rev
        elif design.status_code == 404: logging.error(f'<Response [404]> Not Found. Document Missing {design_doc_name}')
        else:
            status_str = str(design)+str(design.content)
            logging.error(status_str)
        return 

    def DeleteDesignDoc(self, design_doc_name):
        try: doc, _id, _rev = self.DesignDoc(design_doc_name)
        except: return False
        url_id = posixpath.join(self.url, _id)
        #print(url_id+'?rev='+_rev)
        rm = requests.delete(url_id+'?rev='+_rev)
        if rm.status_code == 200: 
            logging.info('<Response [200]> Delete Ok')
            return True
        else:
            status_str = str(rm)+str(rm.content)
            logging.error(status_str)
            return False
        
    def Query(self, url, design_doc_name, search, out_args, eq_all, qtype, datatype=None):
        #out_args = [args.cmdprint, args.outcsv, args.outjson, args.outdir]
        count = 0
        for view in search:
            if 'Site of biopsy/surgery' in view:
                view = view.replace('Site of biopsy/surgery', 'Site of biopsy%2Fsurgery')
            pull = requests.get('{}/_design/{}/_view/{}'.format(url, design_doc_name, view))
            if 'Site of biopsy%2Fsurgery' in view: view = view.replace('Site of biopsy%2Fsurgery', 'Site of biopsy/surgery')
            #print(pull.headers)

            py_dict = json.loads(pull.text)
            number = py_dict["total_rows"]  
            files = py_dict["rows"] #array of jsons
            if qtype == 'm':
                files = self.MultiFilter(files, view)
                number = len(files)
            if qtype == 'e' or qtype == 'l' or qtype == 'g':
                if datatype == None: logging.warning('datatype argument not passed')
                else:
                    new_list, true_list, equal, number = self.Equal_Compare_Filter(qtype, files, view, datatype[count])
                    if eq_all == True: files = new_list
                    else: files = true_list
                    count += 1
            
            if qtype == 'e' or qtype == 'l' or qtype== 'g': #to do es
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
                
    def MultiFilter(self,files, view):
        views = view.split("&")
        files = files
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
        for view in views:
            if view != '_id': #from  view name
                for entry in new_list:
                    py_dict = entry
                    py_dict[view] = None
        for file in files:
            py_dict = file
            report_id = py_dict["id"] #_id online
            key = py_dict["key"]
            value = py_dict["value"]
            #print(report_id, key, value)
            for entry in new_list:
                new_dict = entry
                if report_id == new_dict["_id"] and key != '_id':
                    new_dict[key] = value
        return new_list
    
    def Equal_Compare_Filter(self, qtype, files, view, datatype_tuple):
        files = files
        view_equal = view
        if qtype == 'e': view, equal = view.split("=")   
        elif qtype == 'l': view, equal = view.split("<")   
        elif qtype == 'g': view, equal = view.split(">")
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
        headers = [view, view_equal]
        for entry in new_list:
            for header in headers:
                if header != '_id':
                    py_dict = entry
                    py_dict[header] = None
        for file in files:
            py_dict = file
            report_id = py_dict["id"] #_id online
            key = py_dict["key"]
            value = py_dict["value"]
            #print(report_id, key, value)
            for entry in new_list:
                new_dict = entry
                if report_id == new_dict["_id"] and key != '_id':
                    if key == 'bool': new_dict[view_equal] = value
                    else: new_dict[view] = value
        true_list = []
        equal=0
        for query in new_list:
            check_dict = query
            if check_dict[f"{view_equal}"] == True:
                true_list.append(query)
                equal += 1
        number = int(len(files)/2) #b/c query for key and bool comparison so document appears twice
        return new_list, true_list, equal, number

    def OutDir(self):
        run_path = os.path.realpath(__file__) 
        base = run_path.split("/")
        base = base[:-1]
        base = "/".join(base)
        if os.path.exists(posixpath.join(base, 'extract')) == False:
            os.mkdir(posixpath.join(base, 'extract'))
        out_dir = posixpath.join(base, 'extract')
        return out_dir

    def OutJSON(self, design_doc_name, view, files, out_dir): #note contained within array
        if 'Site of biopsy/surgery' in view:
            view = view.replace('Site of biopsy/surgery','Site of biopsy+surgery')
        out_name_doc = self.OutNameClean(design_doc_name)
        out_name_view = self.OutNameClean(view)
        out_name = f'{out_name_doc}_{out_name_view}'
        out_path = f'{posixpath.join(out_dir,out_name)}.json'
        json_str = json.dumps(files, indent= 4)
        with open(out_path, 'w') as outfile:
            outfile.write(json_str)
        return out_path

    def OutCSV(self, design_doc_name, view, files, out_dir):
        if 'Site of biopsy/surgery' in view:
            view = view.replace('Site of biopsy/surgery','Site of biopsy+surgery')
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

    def OutNameClean(self, out_name):
        out_name = out_name.replace(" ", "")
        out_name = out_name.replace("&", "") #added from design
        out_name = out_name.replace("=", "") #added from design
        out_name = out_name.replace("<", "") #added from design
        out_name = out_name.replace(">", "") #added from design
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
        if len(search) > 0: print() #clean seperate of views
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


