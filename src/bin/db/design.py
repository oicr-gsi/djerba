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
     #def __init__(self, db='test', base='http://admin:cgi@127.0.0.1:5984/', level=logging.INFO, log_path=None, filename=__name__):
     def __init__(self, db='djerba', base='http://admin:djerba123@10.30.133.78:5984/', level=logging.INFO, log_path=None, filename=__name__):
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
          
     def Array(self, filter_type):
          types = ['s','single','d','double','m','multi','e','equal','es','equals']
          if filter_type in types: 
               logging.debug('Valid filter type. Display example and get user input')
               if filter_type == 's' or filter_type == 'single':
                    print(" <separate multiple views w comma>  <access nested dictionaries w forwardslash>", '\n',
                         " i.e. report/assay_type, report/patient_info/Study, supplementary/config/discovered/ploidy", '\n')
                    query = input("Single Filter: ")
                    return query
               elif filter_type == 'd' or filter_type == 'double':         
                    print(" <separate multiple views w comma> <access nested dictionaries w forwardslash> <enter filters like tuple>", '\n',
                    " i.e. (_id, report/failed), (report/assay_type, report/patient_info/Study), (report/patient_info/Primary cancer, report/patient_info/Genetic Sex)", '\n')
                    query = input ('Double Filter: ')
                    return query
               elif filter_type == 'm' or filter_type == 'multi':
                    print(" <separate filters with comma and multiple views w @> <access nested dictionaries w forwardslash>", '\n',
                    " i.e. _id, report/failed, report/author @ report/assay_type, report/patient_info/Study, report/patient_info/Primary cancer, report/patient_info/Genetic Sex @ report/patient_info/Site of biopsy/surgery", '\n')
                    query = input ('Filter Multiple: ')
                    return query
               elif filter_type == 'e' or filter_type == 'equal': ## TO DO
                    print(" <separate multiple views w comma> <access nested dictionaries w forwardslash> <enter filters like tuple>", '\n',
                    " i.e. (report/failed, true), (report/author, Felix Beaudry), (report/oncogenic_somatic_CNVs/Total variants, 35), (report/patient_info/Site of biopsy/surgery, Liver)", '\n')
                    query = input('Equal: ')  
                    return query          
               elif filter_type == 'es' or filter_type == 'equals': ## TO DO
                    print(" <separate multiple views w comma> <access nested dictionaries w forwardslash> <enter filters like tuple>", '\n',
                         " i.e. (_id, test) | (report/failed, true) | (report/author, Bob), (report/author, Felix Beaudry)|(report/oncogenic_somatic_CNVs/Total variants, 35) ", '\n')
                    query = input ('Equals: ')
                    s = query.split("|")
                    a = [""]
                    index = 0
                    view_num = 0
                    while index < len(s):
                         sep = s[index].count(",") 
                         if sep == 1:
                              a[view_num] = a[view_num] + s[index]
                         else:
                              temp = s[index].split(",")
                              prev = ','.join(temp[:2])
                              a[view_num] = a[view_num] + prev
                              view_num += 1
                              nex = ','.join(temp[2:])
                              a.append(nex)
                         index += 1
                    no_space = []
                    for i in a:
                         i = i.strip()
                         no_space.append(i)
                    sep_view = []
                    for i in no_space:
                         i = i.replace(")", ")|")
                         sep_view.append(i)
                    array = []
                    for i in sep_view:
                         i = i.strip()
                         i = i.rstrip(i[-1])
                         array.append(i)
                    return array
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

     #views = ["(_id,test)|(report/failed,true)|(report/author,Bob)", "(report/author,Felix Beaudry)|(report/oncogenic_somatic_CNVs/Total variants,35)"]
     #views = ["(report/patient_info/Primary cancer, Pancreatic Adenocarcinoma) | (report/sample_info_and_quality/Coverage (mean), 100) | (report/purity_failure, false)"]
     def Equals(self, design_doc_name, query, out_args, eq_all):  
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
               "note": "", #comment
          }
          viewsEqs_name = []
          nkey = []
          nval = []
          nvaltype = []
          for v in array:
               temp_name = []
               key = []
               value = []
               split = v.split("|")
               rm = []
               for s in split: 
                    s = s.replace("(", "")
                    s = s.replace(")", "")
                    rm.append(s.strip())
               for s in rm:
                    temp = s.split(",")
                    tempstr = temp[0]
                    tempkey = tempstr.split("/")
                    lastkey = tempkey[-1]
                    key.append(temp[0].strip())
                    value.append(temp[1].strip())
                    temp_name.append(lastkey.strip())
               joined = ""
               for s in temp_name:
                    if s != temp_name[-1]: joined += f"{s}/" 
                    else: joined += f"{s}="
               for s in value:
                    if s != value[-1]: joined += f"{s}/" 
                    else: joined += f"{s}"
               viewsEqs_name.append(joined)
               nkey.append(key)
               nval.append(value)
          for i in range(len(array)):
               key = nkey[i]
               val = nval[i]
               for n in range(len(key)):
                    temp = key[n]
                    temp = temp.split("/")
                    string = ""
                    for t in temp: string += f"['{t}']" 
                    key[n] = string
               valtype = []
               for v in val:
                    if self.isNumber(v) == True:
                         if v.count(".") == 1: num = float(v)
                         else: num = int(v)
                         valtype.append(num)
                    elif type(self.isBool(v)) == bool:
                         boolean = self.isBool(v)
                         valtype.append(json.dumps(boolean))
                    else:
                         valtype.append(f"'{v.strip()}'")

               nvaltype.append(valtype)
          for i in range(len(array)):
               key = nkey[i]
               val = nvaltype[i]
               design["views"][f"{viewsEqs_name[i]}"] = {
                    "map": "function (doc) { if(" 
               }
               for j in range(len(key)):
                    #print(key[j], val[j], type(val[j]))
                    if j != len(key)-1: design["views"][f"{viewsEqs_name[i]}"]["map"] += f"doc{key[j]} == {val[j]} && "
                    else: design["views"][f"{viewsEqs_name[i]}"]["map"] += f"doc{key[j]} == {val[j]}" + " ) { "
               for j in range(len(key)):
                    design["views"][f"{viewsEqs_name[i]}"]["map"] += f"emit(doc{key[j]}, doc{key[j]}=={val[j]});"
               design["views"][f"{viewsEqs_name[i]}"]["map"] += "} }"
     
          headers = {'Content-Type': 'application/json'}
          submit = requests.post(url=self.url, headers=headers, json=design)
          status_str = str(submit)+str(submit.content)
          if submit.status_code == 201: logging.info('<Response [201]> Upload Ok')
          elif submit.status_code == 409: logging.warning('<Response [409]> Document Update Conflict')
          else: logging.error(status_str)
     
     def Equal(self, design_doc_name, query, out_args, eq_all): 
          #out_args = [args.cmdprint, args.outcsv, args.outjson, args.outdir]
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
               "note": "", #comment
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
          # Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
          return
     
     def Multi(self, design_doc_name, query, out_args, eq_all):
          #out_args = [args.cmdprint, args.outcsv, args.outjson, args.outdir]
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
               "note": "", #comment
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

     def Double(self, design_doc_name, query, out_args, eq_all): 
          #out_args = [args.cmdprint, args.outcsv, args.outjson, args.outdir]
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
               "note": "", #comment
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
          views2_name = []
          for v in g:
               first = v[0]
               second = v[1]
               first = first.split("/")
               second = second.split("/")         
               first = [i.strip() for i in first]
               second = [i.strip() for i in second]
               views2_name.append(f'{first[-1]}&{second[-1]}')
          for j in range(len(views2_name)):
               if 'Site of biopsy+surgery' in views2_name[j]:
                    views2_name[j] = views2_name[j].replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
          for i in range(len(g)):
               one = g[i][0].split("/")
               one = [i.strip() for i in one]
               two = g[i][1].split("/")
               two = [i.strip() for i in two]
               string_one = "doc"
               for j in one: string_one += f"['{j}']"
               string_two = "doc"
               for j in two: string_two += f"['{j}']"
               if 'Site of biopsy+surgery' in string_one: string_one = string_one.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
               if 'Site of biopsy+surgery' in string_two: string_two = string_two.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
               design["views"][f"{views2_name[i]}"] = {
                    "map": 'function (doc) { emit(' + f'{string_one},{string_two})' + ';} '
               } 
          headers = {'Content-Type': 'application/json'}
          submit = requests.post(url=self.url, headers=headers, json=design)
          status_str = str(submit)+str(submit.content)
          if submit.status_code == 201: logging.info('<Response [201]> Upload Ok')
          elif submit.status_code == 409: logging.warning('<Response [409]> Document Update Conflict')
          else: logging.error(status_str)
          
          Pull(self.db, self.base).Query(self.url, design_doc_name, views2_name, out_args, eq_all, qtype='d')
          Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
          return

     def Single(self, design_doc_name, query, out_args, eq_all): 
          #out_args = [args.cmdprint, args.outcsv, args.outjson, args.outdir]
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
               "note": "", #comment
          }
          if 'Site of biopsy/surgery' in query:
               query = query.replace('Site of biopsy/surgery', 'Site of biopsy+surgery')
          arr = query.split(",")
          arr = [i.strip() for i in arr] 
          search = []
          for v in arr:
               split = v.split("/")
               split = [i.strip() for i in split] 
               string = "doc"
               for i in split: 
                    string += f"['{i}']"
               if 'Site of biopsy+surgery' in split[-1]: split[-1] = split[-1].replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
               if 'Site of biopsy+surgery' in string: string = string.replace('Site of biopsy+surgery', 'Site of biopsy/surgery')
               design["views"][f"{split[-1]}"] = {"map": "function (doc) {\n  emit "+f" ('{split[-1]}', {string}) "+" ;\n}"} 
               search.append(split[-1])
          headers = {'Content-Type': 'application/json'}
          submit = requests.post(url=self.url, headers=headers, json=design)
          status_str = str(submit)+str(submit.content)
          if submit.status_code == 201: logging.info('<Response [201]> Upload Ok')
          elif submit.status_code == 409: logging.warning('<Response [409]> Document Update Conflict')
          else: logging.error(status_str)

          Pull(self.db, self.base).Query(self.url, design_doc_name, search, out_args, eq_all, qtype ='s')
          Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
          return

     def SetUp(self):
          parser = argparse.ArgumentParser()
          parser.add_argument('filter', help='word or letter accepted: single(s), double(d), multi(m), equal(e), or equals(es)')#, type=str, action="store", dest="filter", required=True)
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
               query = self.Array(args.filter)
               if query != '': notblank = True
               timed_out += 1
          if args.filter == 'multi' or args.filter == 'm': self.Multi(design_doc_name, query, out_args, eq_all)
          elif args.filter == 'single' or args.filter == 's': self.Single(design_doc_name, query, out_args, eq_all)
          elif args.filter == 'double' or args.filter == 'd': self.Double(design_doc_name, query, out_args, eq_all)
          elif args.filter == 'equal' or args.filter == 'e': self.Equal(design_doc_name, query, out_args, eq_all)
          # elif args.filter == 'equals' or args.filter == 'es': self.Equals(design_doc_name, query, out_args, eq_all)
          
          '''other'''
          # try: data_base, total_doc, del_doc = Pull(self.db, self.base).DBStat()
          # except: logging.warning('database error')
          # try: doc, _id, _rev = Pull(self.db, self.base).DesignDoc(design_doc_name)
          # except: logging.warning('may not be created yet')
          # del_bool = Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
          # if del_bool == False: logging.warning('error w delete design doc')
          return

if __name__ == "__main__":
     Design().SetUp()

'''
#dictionary comprehension, more condensed   !!!
design["views"] = { v: {"map": "function (doc) {\n  emit(doc._id, doc." + f"{v}" + ");\n}"} for v in views }

     # import json
     # file_name = 'djerba_report_machine.pretty'
     # with open(f'/home/ltoy/Desktop/couch/{file_name}.json') as json_file:
     #      data = json.load(json_file)    
'''
#s = "(_id,test) | (report/failed, true) | (report/author, Bob) , (report/author, Felix Beaudry) | (report/oncogenic_somatic_CNVs/Total variants, 35) "
#s = " (_id,test)|(a,b)|(1/2,3/4/5), (a,a)|(b/b/b,B)|(c/c/c/c,D), (hello,hi)|(name,age),  (,)|(blah,a)|(i/x,one) |  ( a,b )"
#views = [" (_id,test)|(a,b)|(1/2,3/4/5)", "(a,a)|(b/b/b,B)|(c/c/c/c,D)", "(hello,hi)|(name,age)" , " (,)|(blah,a)|(i/x,one) |  ( a,b )"]
#views_numcheck = [ "(report/oncogenic_somatic_CNVs/Total variants,35)"]
#views_strcheck = ["(_id,test)|(report/author,Bob)", "(report/author,Felix Beaudry)"]
