import argparse
import requests
import logging
import json
import os
from datetime import datetime
from posixpath import join
from pull import Pull

#http://127.0.0.1:5984/_utils/#login - 000
#http://10.30.133.78:5984/_utils/#login - djerba
#dbs = 'http://admin:cgi@127.0.0.1:5984/_all_dbs'

class Design():
     #def __init__(self, db='djerba', base='http://admin:djerba123@10.30.133.78:5984/', level=logging.WARNING, log_path=None, filename=__name__):
     def __init__(self, db='test', base='http://admin:cgi@127.0.0.1:5984/', level=logging.WARNING, log_path=None, filename=__name__):
          self.db = db
          self.base = base
          self.url = join(self.base,self.db)          
          self.level = level
          self.filename = filename
          self.log_path = log_path
          if log_path != None:
               file_path = join(self.log_path, self.filename)
               file_path += '.log'
          else: file_path = None
          logging.basicConfig(level=level, filename=file_path, format=f'%(asctime)s:%(filename)s:%(levelname)s: %(message)s', datefmt='%Y-%m-%d_%H:%M:%S')
          
     def User_Query_Input(self, filter_type):
          types = ['m','multi','e','equal', 'l', 'less', 'g', 'great']
          if filter_type in types: 
               logging.debug('Valid filter type. Display example and get user input')
               if filter_type == 'm' or filter_type == 'multi':
                    print(" <separate filters with comma and multiple views w @> <access nested dictionaries w forwardslash>", '\n',
                    " i.e. report/failed, report/author @ report/assay_type, report/patient_info/Study, report/patient_info/Primary cancer, report/patient_info/Genetic Sex @ report/patient_info/Site of biopsy/surgery", '\n')
                    query = input ('Filter Multiple: ')
                    return query
               elif filter_type == 'e' or filter_type == 'equal': 
                    print(" <separate multiple views w comma> <access nested dictionaries w forwardslash> <enter filters like tuple>", '\n',
                    " i.e. (report/failed, true), (report/author, Felix Beaudry), (report/oncogenic_somatic_CNVs/Total variants, 35), (report/patient_info/Site of biopsy/surgery, Liver)", '\n')
                    query = input('Equal: ')  
                    return query
               elif  filter_type == 'l' or filter_type == 'less' or filter_type == 'g' or filter_type == 'great':
                    print(" <separate multiple views w comma> <access nested dictionaries w forwardslash> <enter filters like tuple>", '\n',
                    " i.e. (report/oncogenic_somatic_CNVs/Total variants, 35)")
                    if filter_type == 'l' or filter_type == 'less': query = input('Less: ')  
                    if filter_type == 'g' or filter_type == 'great': query = input('Great: ')  
                    return query
          else: 
               logging.error('Invalid filter type')
          return 

     def isNumber(self, n):
          logging.debug('Check if string is number, return boolean')
          n = n.strip()
          if n.isnumeric() == True: return True
          if n.count('.') == 1 or n.count('.') == 0:
               if n.count('.') == 1: 
                    n = n.replace('.','')
                    if n.isnumeric() == True: return True
               elif n.find('-') != -1 and n[0] == '-': 
                    n = n.replace('-','')
                    if n.isnumeric() == True: return True
          else: return False 

     def isBool(self, b):  
          logging.debug('Return corresponding bool from str')
          b = b.strip()
          if b == 'True' or b == 'true':
               true_bool = bool(b)
               return true_bool
          elif b == 'False' or b == 'false':
               false_bool = bool(b)
               false_bool = False
               return false_bool
          else: return  

     def Compare(self, qtype, design_doc_name, query, out_args, eq_all): 
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
          }
          if 'Site of biopsy/surgery' in query:
               query = query.replace('Site of biopsy/surgery', 'Site of biopsy+surgery')
          if query.count(",") > 1: #multi-view
               l = query.split(",")
               l = [i.strip() for i in l]
               grouped = [tuple(l[i:i+2]) for i in range(0, len(l), 2)]
          else: #single-view
               l = query.split(",")
               l=[i.strip() for i in l]
               grouped = [tuple(l)]
          g = []
          for i in grouped: 
               one = i[0]
               two = i[1]
               one = one.replace("(","", 1)
               rev = two[::-1]
               rev = rev.replace(")", "", 1)
               two = rev[::-1]
               g.append((one,two))
          viewsEq_name = []
          for v in g:
               first = v[0]
               second = v[1]
               first = first.split("/")
               second = second.split("/")         
               first = [i.strip() for i in first]
               second = [i.strip() for i in second]
               if qtype == 'l': viewsEq_name.append(f'{first[-1]}<{second[-1]}')
               if qtype == 'g': viewsEq_name.append(f'{first[-1]}>{second[-1]}')
          for j in range(len(viewsEq_name)):
               if 'Site of biopsy+surgery' in viewsEq_name[j]:
                    viewsEq_name[j] = viewsEq_name[j].replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
          datatype = []
          for i in range(len(g)):
               one = g[i][0].split("/")
               one = [i.strip() for i in one]
               two = g[i][1].split("/")
               two = [i.strip() for i in two]
               string_one = "doc"
               for j in one: string_one += f"['{j}']"
               key = one[-1] 
               if 'Site of biopsy+surgery' in string_one: string_one = string_one.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
               if 'Site of biopsy+surgery' in key: key = key.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
               if self.isNumber(two[0]) == True and qtype == 'g':
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{string_one} > {two[0]});" + "emit(" + f"'{key}',{string_one}) "+";} }" #for number 
                    }
                    val = float(two[0])
                    if two[0].count(".") == 0 and val%1 == 0.0: val = int(two[0])
               elif self.isNumber(two[0]) == True and qtype == 'l':
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{string_one} < {two[0]});" + "emit(" + f"'{key}',{string_one}) "+";} }" #for number 
                    }
                    val = float(two[0])
                    if two[0].count(".") == 0 and val%1 == 0.0: val = int(two[0])
               datatype.append((key,val))
          headers = {'Content-Type': 'application/json'}
          submit = requests.post(url=self.url, headers=headers, json=design)
          status_str = str(submit)+str(submit.content)
          if submit.status_code == 201: logging.info('<Response [201]> Upload Ok')
          elif submit.status_code == 409: logging.warning('<Response [409]> Document Update Conflict')
          else: logging.error(status_str)
          
          Pull(self.db, self.base).Query(self.url, design_doc_name, viewsEq_name, out_args, eq_all, qtype=qtype, datatype=datatype)
          #Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
          return

     def Equal(self, design_doc_name, query, out_args, eq_all): 
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
          }
          if 'Site of biopsy/surgery' in query:
               query = query.replace('Site of biopsy/surgery', 'Site of biopsy+surgery')
          if query.count(",") > 1: #multi-view
               l = query.split(",")
               l = [i.strip() for i in l]
               grouped = [tuple(l[i:i+2]) for i in range(0, len(l), 2)]
          else: #single-view
               l = query.split(",")
               l=[i.strip() for i in l]
               grouped = [tuple(l)]
          g = []
          for i in grouped: 
               one = i[0]
               two = i[1]
               one = one.replace("(","", 1)
               rev = two[::-1]
               rev = rev.replace(")", "", 1)
               two = rev[::-1]
               g.append((one,two))
          viewsEq_name = []
          for v in g:
               first = v[0]
               second = v[1]
               first = first.split("/")
               second = second.split("/")         
               first = [i.strip() for i in first]
               second = [i.strip() for i in second]
               viewsEq_name.append(f'{first[-1]}={second[-1]}')
          for j in range(len(viewsEq_name)):
               if 'Site of biopsy+surgery' in viewsEq_name[j]:
                    viewsEq_name[j] = viewsEq_name[j].replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
          datatype = []
          for i in range(len(g)):
               one = g[i][0].split("/")
               one = [i.strip() for i in one]
               two = g[i][1].split("/")
               two = [i.strip() for i in two]
               string_one = "doc"
               for j in one: string_one += f"['{j}']"
               key = one[-1] 
               if 'Site of biopsy+surgery' in string_one: string_one = string_one.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
               if 'Site of biopsy+surgery' in key: key = key.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
               if self.isNumber(two[0]) == True:
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{string_one} == {two[0]});" + "emit(" + f"'{key}',{string_one}) "+";} }" #for number 
                    }
                    val = float(two[0])
                    if two[0].count(".") == 0 and val%1 == 0.0: val = int(two[0])
               elif type(self.isBool(two[0])) == bool:
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{string_one} == {json.dumps(self.isBool(two[0]))});" + "emit(" + f"'{key}',{string_one}) "+";} }" #for bool
                    }
                    val = self.isBool(two[0])
               else:
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{string_one} == '{two[0]}');"+"emit(" + f"'{key}',{string_one}) "+";} }" #for string 
                    }
                    val = two[0]
               datatype.append((key,val))
          headers = {'Content-Type': 'application/json'}
          submit = requests.post(url=self.url, headers=headers, json=design)
          status_str = str(submit)+str(submit.content)
          if submit.status_code == 201: logging.info('<Response [201]> Upload Ok')
          elif submit.status_code == 409: logging.warning('<Response [409]> Document Update Conflict')
          else: logging.error(status_str)
          
          Pull(self.db, self.base).Query(self.url, design_doc_name, viewsEq_name, out_args, eq_all, qtype='e', datatype=datatype)
          #Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
          return
     
     def Multi(self, design_doc_name, query, out_args, eq_all):
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
          }    
          if 'Site of biopsy/surgery' in query:
               query = query.replace('Site of biopsy/surgery', 'Site of biopsy+surgery')
          views = query.split("@")
          views = [i.strip() for i in views]
          viewF_name = []
          for view in views:
               tempkey = view.split(",")
               tempkey = [i.strip() for i in tempkey]
               name = ""
               for key in tempkey:
                    nested = key.split("/")
                    nested = [i.strip() for i in nested]
                    for j in range(len(nested)):
                         if nested[j] == 'Site of biopsy+surgery':
                              nested[j] = nested[j].replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
                    if key == tempkey[0]: name += f'{nested[-1]}'
                    else: name += f'&{nested[-1]}'
               viewF_name.append(name)
          for i in range(len(views)):
               keys = views[i].split(",")
               keys = [i.strip() for i in keys]
               count = 0 
               combined = ""
               for nested in keys:
                    individual = 'emit(doc'
                    key = nested.split("/")
                    key = [i.strip() for i in key]
                    individual = f"emit('{key[-1]}',doc"
                    if 'Site of biopsy+surgery' in individual:
                         individual = individual.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
                    for k in key:
                         if 'Site of biopsy+surgery' in k:
                              k = k.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
                         individual += f"['{k}']"
                    individual += ')'
                    combined += f'{individual};'
                    count += 1
               design["views"][f"{viewF_name[i]}"] = {
                    "map": "function (doc) {" + f"{combined}" + "} "
               }
          headers = {'Content-Type': 'application/json'}
          submit = requests.post(url=self.url, headers=headers, json=design)
          status_str = str(submit)+str(submit.content)
          if submit.status_code == 201: logging.info('<Response [201]> Upload Ok')
          elif submit.status_code == 409: logging.warning('<Response [409]> Document Update Conflict')
          else: logging.error(status_str)
          
          Pull(self.db, self.base).Query(self.url, design_doc_name, viewF_name, out_args, eq_all, qtype ='m')
          #Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
          return

     def SetUp(self):
          parser = argparse.ArgumentParser()
          parser.add_argument('filter', help='word or letter accepted: multi(m), equal(e), less(l), great(g)')#, type=str, action="store", dest="filter", required=True)
          parser.add_argument("-n", "--name", help="design doc name, default is test", action="store", type=str, dest="name", default='test')
          parser.add_argument("-p", "--print", help="print to terminal", action="store_true", dest="cmdprint", default=False)
          parser.add_argument("-c", "--csv", help="save query as CSV", action="store_true", dest="outcsv", default=False)
          parser.add_argument("-j", "--json", help="save query as JSON", action="store_true", dest="outjson", default=False)
          parser.add_argument("-d", "--dir", help="output directory, default is file path", action="store", type=str, dest="dir", default=None)
          parser.add_argument("-a", "--all", help="show all results for equal(e) filter, default is False", action="store_true", dest="all", default=False)
          args = parser.parse_args()
          design_doc_name = args.name
          out_args = [args.cmdprint, args.outcsv, args.outjson, args.dir]
          eq_all = args.all
          if args.dir != None:
               if os.path.exists(args.dir) != True: 
                    logging.error('out_dir path does not exist')
                    return
               if os.path.isdir(args.dir) != True: 
                    logging.error('out_dir is not a directory')
                    return
          timed_out = 0
          notblank = False 
          while notblank == False and timed_out < 6:
               if timed_out == 5:
                    logging.error('Timed out. 5 blank query inputs')
                    return
               query = self.User_Query_Input(args.filter)
               if query != '': notblank = True
               timed_out += 1
          if args.filter == 'multi' or args.filter == 'm': self.Multi(design_doc_name, query, out_args, eq_all)
          elif args.filter == 'equal' or args.filter == 'e': self.Equal(design_doc_name, query, out_args, eq_all)
          elif args.filter == 'less' or args.filter == 'l': self.Compare('l', design_doc_name, query, out_args, eq_all)
          elif args.filter == 'great' or args.filter == 'g': self.Compare('g', design_doc_name, query, out_args, eq_all)
          return

if __name__ == "__main__":
     Design().SetUp()

#'''other functions in pull.py'''
# try: data_base, total_doc, del_doc = Pull(self.db, self.base).DBStat()
# except: logging.warning('database error')
# try: doc, _id, _rev = Pull(self.db, self.base).DesignDoc(design_doc_name)
# except: logging.warning('may not be created yet')
# del_bool = Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
# if del_bool == False: logging.warning('error w delete design doc')