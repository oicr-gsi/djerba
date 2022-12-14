import argparse
import requests
import logging
import json
import os
from datetime import datetime
from posixpath import join
from pull import Pull

#http://10.30.133.78:5984/_utils/#login - djerba company secure instance (includes djerba and djerba_test databases)
#http://127.0.0.1:5984/_utils/#login - 000 seperate instance for initial dev purposes and testing 

class Design():
     ''' change location of database here with db and base'''
     def __init__(self, db='djerba', base='http://admin:djerba123@10.30.133.78:5984/', level=logging.WARNING, log_path=None, filename=__name__):
     #def __init__(self, db='test', base='http://admin:cgi@127.0.0.1:5984/', level=logging.WARNING, log_path=None, filename=__name__):
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

     def CheckCommandLineArgumentsAndGetQueryOrCompleteOtherModeRequest(self, args):
          '''validate user cmd line input'''
          qtype = args.mode
          design_doc_name = args.name 
          modes = ['stat', 's', 'del', 'd', 'm','multi', 'e','equal', 'l', 'less', 'g', 'great']
          if qtype not in modes:
               logging.error('invalid mode, try python3 design.py --help')
               return False, None, None, None, None, None
          #database status and delete design document mode
          if qtype == 'stat' or qtype =='s' or qtype == 'del' or qtype == 'd':
               self.DatabaseStatAndDesignDocDelete(qtype, design_doc_name)
               return False, None, None, None, None, None
          #filter modes
          eq_all = args.all          
          out_args = [args.cmdprint, args.outcsv, args.outjson, args.dir]
          if design_doc_name == None:
               logging.error('name of design document not specified, use -n flag')
               return False, None, None, None, None, None
          if out_args[3] != None:
               if os.path.exists(out_args[3]) != True: 
                    logging.error('out_dir path does not exist')
                    return False, None, None, None, None, None
               if os.path.isdir(out_args[3]) != True: 
                    logging.error('out_dir is not a directory')
                    return False, None, None, None, None, None
          timed_out = 0
          notblank = False
          while notblank == False and timed_out < 6:
               if timed_out == 5:
                    logging.error('Timed out. 5 blank query inputs')
                    return False, None, None, None, None, None
               query = self.User_Query_Input(qtype) 
               if query != '': notblank = True
               timed_out += 1
          return True, qtype, design_doc_name, query, out_args, eq_all

     def Compare(self, qtype, design_doc_name, query, out_args, eq_all):
          '''main method for filters with operator, equal or less or great''' 
          query = Pull().CheckAndSwitchForwardSlashOrPlus(query)
          tuple_list_of_key_and_value = self.ConvertQueryIntoListOfTuples(query)
          tuple_list_of_key_and_value = self.RemoveBracketsInQuery(tuple_list_of_key_and_value)
          viewsEq_name = self.GetViewName(qtype, tuple_list_of_key_and_value)
          
          if qtype == 'e':
               design, datatype_preserved = self.Equal_Putting_Key_Value_Into_Map_Views(design_doc_name, viewsEq_name, tuple_list_of_key_and_value)
          elif qtype == 'l' or qtype == 'g':
               design, datatype_preserved = self.LessAndGreat_Putting_Key_Value_Into_Map_Views(qtype, design_doc_name, viewsEq_name, tuple_list_of_key_and_value)
          
          self.UploadDesignDoc(design)
          Pull(self.db, self.base).Query(self.url, design_doc_name, viewsEq_name, out_args, eq_all, qtype=qtype, datatype=datatype_preserved)
          return

     def LessAndGreat_Putting_Key_Value_Into_Map_Views(self, qtype, design_doc_name, viewsEq_name, tuple_list_of_key_and_value):
          '''create design document javascript for compare filters less or great (value can only be a number)'''
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
          }
          datatype_preserved = []
          for i in range(len(tuple_list_of_key_and_value)):
               nested_key_list = tuple_list_of_key_and_value[i][0].split("/")
               nested_key_list = [i.strip() for i in nested_key_list]
               val_str = tuple_list_of_key_and_value[i][1]
               nested_key_string = "doc"
               for key in nested_key_list: nested_key_string += f"['{key}']"
               key = nested_key_list[-1] 
               nested_key_string = Pull().CheckAndSwitchForwardSlashOrPlus(nested_key_string)
               key = Pull().CheckAndSwitchForwardSlashOrPlus(key)

               if self.isNumber(val_str) == True and qtype == 'g': # > number 
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{nested_key_string} > {val_str});" + "emit(" + f"'{key}',{nested_key_string}) "+";} }" 
                    }
                    val_num = float(val_str)
                    if val_str.count(".") == 0 and val_num%1 == 0.0: val_num = int(val_str)
               elif self.isNumber(val_str) == True and qtype == 'l': # < number 
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{nested_key_string} < {val_str});" + "emit(" + f"'{key}',{nested_key_string}) "+";} }" 
                    }
                    val_num = float(val_str)
                    if val_str.count(".") == 0 and val_num%1 == 0.0: val_num = int(val_str)
               datatype_preserved.append((key,val_num))
          return design, datatype_preserved

     def ConvertQueryIntoListOfTuples(self, query):
          '''seperate key and value for comparison filters equal or less or great'''
          if query.count(",") > 1: #multi-view
               seperate_query_at_comma = query.split(",")
               seperate_query_at_comma = [i.strip() for i in seperate_query_at_comma]
               tuple_list = [tuple(seperate_query_at_comma[i:i+2]) for i in range(0, len(seperate_query_at_comma), 2)]
          else: #single-view
               seperate_query_at_comma = query.split(",")
               seperate_query_at_comma =[i.strip() for i in seperate_query_at_comma]
               tuple_list = [tuple(seperate_query_at_comma)]
          return tuple_list

     def DatabaseStatAndDesignDocDelete(self, qtype, design_doc_name = None):
          '''modes for database stats or deleting design doc'''
          if qtype == 'stat' or qtype == 's':
               db, total_doc, del_doc = Pull(self.db, self.base).DatabaseStat()
               stats = f'{db.capitalize()} Database. Total Doc (including design etc.) = {total_doc}. Deleted Doc = {del_doc}'            
               print(stats)
               print(self.url)
          elif qtype == 'del' or qtype == 'd':
               if design_doc_name == None: 
                    logging.error('name of design document to delete not specified, use -n flag')
               else: 
                    deleted_bool = Pull(self.db, self.base).DeleteDesignDoc(design_doc_name)
                    if deleted_bool == True: print(f'Sucessfully deleted "{design_doc_name}" from {self.db} database')
          return

     def Equal_Putting_Key_Value_Into_Map_Views(self, design_doc_name, viewsEq_name, tuple_list_of_key_and_value):
          '''create design document javascript for filters equal, accounting for datatype of string, bool, or number'''
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
          }
          datatype_preserved = []
          for i in range(len(tuple_list_of_key_and_value)):
               nested_key_list = tuple_list_of_key_and_value[i][0].split("/")
               nested_key_list = [i.strip() for i in nested_key_list]
               val_str = tuple_list_of_key_and_value[i][1]
               nested_key_string = "doc"
               for key in nested_key_list: nested_key_string += f"['{key}']"
               key = nested_key_list[-1] 
               nested_key_string = Pull().CheckAndSwitchForwardSlashOrPlus(nested_key_string)
               key = Pull().CheckAndSwitchForwardSlashOrPlus(key)

               if self.isNumber(val_str) == True:
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{nested_key_string} == {val_str});" + "emit(" + f"'{key}',{nested_key_string}) "+";} }" #for number 
                    }
                    val = float(val_str)
                    if val_str.count(".") == 0 and val%1 == 0.0: val = int(val_str)
               elif type(self.isBool(val_str)) == bool:
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{nested_key_string} == {json.dumps(self.isBool(val_str))});" + "emit(" + f"'{key}',{nested_key_string}) "+";} }" #for bool
                    }
                    val = self.isBool(val_str)
               else:
                    design["views"][f"{viewsEq_name[i]}"] = {
                         "map": "function (doc) {"+"{emit('bool'," + f"{nested_key_string} == '{val_str}');"+"emit(" + f"'{key}',{nested_key_string}) "+";} }" #for string 
                    }
                    val = val_str
               datatype_preserved.append((key,val))
          return design, datatype_preserved

     def GetViewName(self, qtype, query2list):
          '''unique and descriptive name for view name, online couch db interface, and later output files'''
          if qtype == 'm':
               view_name = []
               for view in query2list: #list of views
                    list_of_nested_keys = view.split(",")
                    list_of_nested_keys = [i.strip() for i in list_of_nested_keys]
                    name = ""
                    for nested_key in list_of_nested_keys:
                         nested_seperated = nested_key.split("/")
                         nested_seperated = [i.strip() for i in nested_seperated]
                         for j in range(len(nested_seperated)):
                              nested_seperated[j] = Pull().CheckAndSwitchForwardSlashOrPlus(nested_seperated[j])
                         if nested_key == list_of_nested_keys[0]: name += f'{nested_seperated[-1]}'
                         else: name += f'&{nested_seperated[-1]}'
                    view_name.append(name)
          else: #qtype == 'e' or 'l' or 'g'
               view_name = []
               for tupl in query2list: #list of tuples
                    key = tupl[0]
                    val = tupl[1]
                    key = key.split("/")
                    key = [i.strip() for i in key]
                    val = val.strip()
                    if qtype == 'l': view_name.append(f'{key[-1]}<{val}')
                    if qtype == 'g': view_name.append(f'{key[-1]}>{val}')
                    if qtype == 'e': view_name.append(f'{key[-1]}={val}')
               for i in range(len(view_name)): 
                    view_name[i] = Pull().CheckAndSwitchForwardSlashOrPlus(view_name[i]) 
          return view_name

     def isBool(self, b):  
          '''Return corresponding bool from str'''
          b = b.strip()
          if b == 'True' or b == 'true':
               true_bool = bool(b)
               return true_bool
          elif b == 'False' or b == 'false':
               false_bool = bool(b)
               false_bool = False
               return false_bool
          else: return  

     def isNumber(self, n):
          '''Check if string is number, return boolean'''
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

     def Multi(self, qtype, design_doc_name, query, out_args, eq_all):
          '''main method for multi filter'''
          query = Pull().CheckAndSwitchForwardSlashOrPlus(query)    
          list_of_views = query.split("@") 
          list_of_views = [i.strip() for i in list_of_views]
          viewF_name = self.GetViewName(qtype, list_of_views)
          design = self.Multi_Putting_Key_Into_Map_Views(design_doc_name, viewF_name, list_of_views)
          self.UploadDesignDoc(design)          
          Pull(self.db, self.base).Query(self.url, design_doc_name, viewF_name, out_args, eq_all, qtype ='m')
          return

     def Multi_Putting_Key_Into_Map_Views(self, design_doc_name, viewF_name, list_of_views):
          '''create design document javascript for multi filter'''
          design = {
               "_id": "_design/{}".format(design_doc_name),
               "views": {} ,
          }
          for i in range(len(list_of_views)):
               list_of_nested_keys = list_of_views[i].split(",")
               list_of_nested_keys = [j.strip() for j in list_of_nested_keys]
               combined = ""
               for nested_key in list_of_nested_keys:
                    individual = 'emit(doc'
                    keys_seperated = nested_key.split("/")
                    keys_seperated = [j.strip() for j in keys_seperated]
                    individual = f"emit('{keys_seperated[-1]}',doc"
                    individual = Pull().CheckAndSwitchForwardSlashOrPlus(individual)
                    for key in keys_seperated: 
                         key = Pull().CheckAndSwitchForwardSlashOrPlus(key)
                         individual += f"['{key}']"
                    individual += ')'
                    combined += f'{individual};'
               design["views"][f"{viewF_name[i]}"] = {
                    "map": "function (doc) {" + f"{combined}" + "} "
               }
          return design

     def RemoveBracketsInQuery(self, tuple_list_of_key_and_value):
          '''remove brackets from cmd line query key/value tuple like format for operator based filters, equal or less or great'''
          without_brackets = []
          for tupl in tuple_list_of_key_and_value: 
               key = tupl[0]
               val = tupl[1]
               key = key.replace("(","", 1)
               val_reversed = val[::-1]
               val_reversed = val_reversed.replace(")", "", 1)
               val = val_reversed[::-1]
               without_brackets.append((key,val))
          return without_brackets

     def SetUp(self):
          '''first method to set and parse command line arguments'''
          parser = argparse.ArgumentParser()
          parser.add_argument('mode', help='''<word or letter accepted>  [1] Filter = multi(m), equal(e), less(l), great(g). [2] Database Status = stat(s). [3] Delete Design Document = del(d)''')
          parser.add_argument("-n", "--name", help="design doc name", action="store", type=str, dest="name", default=None)
          parser.add_argument("-p", "--print", help="print query to terminal", action="store_true", dest="cmdprint", default=False)
          parser.add_argument("-c", "--csv", help="save query as CSV", action="store_true", dest="outcsv", default=False)
          parser.add_argument("-j", "--json", help="save query as JSON", action="store_true", dest="outjson", default=False)
          parser.add_argument("-d", "--dir", help="output directory, default is file path", action="store", type=str, dest="dir", default=None)
          parser.add_argument("-a", "--all", help="show all files for equal/less/great, default is False", action="store_true", dest="all", default=False)
          args = parser.parse_args()
          valid, qtype, design_doc_name, query, out_args, eq_all = self.CheckCommandLineArgumentsAndGetQueryOrCompleteOtherModeRequest(args)
          if valid == False: return

          if qtype == 'multi' or qtype == 'm': self.Multi('m', design_doc_name, query, out_args, eq_all)
          elif qtype == 'equal' or qtype == 'e': self.Compare('e', design_doc_name, query, out_args, eq_all)
          elif qtype == 'less' or qtype == 'l': self.Compare('l', design_doc_name, query, out_args, eq_all)
          elif qtype == 'great' or qtype == 'g': self.Compare('g', design_doc_name, query, out_args, eq_all)
          return

     def UploadDesignDoc(self, design):
          '''HTTP post of design document to database'''
          headers = {'Content-Type': 'application/json'}
          submit = requests.post(url=self.url, headers=headers, json=design)
          status_str = str(submit)+str(submit.content)
          if submit.status_code == 201: logging.info('<Response [201]> Design Document Upload Ok')
          elif submit.status_code == 409: logging.warning('<Response [409]> Design Document Update Conflict.')
          else: logging.error(status_str)
          return

     def User_Query_Input(self, filter_type):
          '''display format instructions and get user input query as string'''
          types = ['m','multi', 'e','equal', 'l', 'less', 'g', 'great']
          if filter_type in types: 
               logging.debug('Valid filter type. Display example and get user input')
               if filter_type == 'm' or filter_type == 'multi':
                    print(" <access nested keys w forwardslash> <separate filters with comma (same view) and different views w @> ", '\n',
                    " i.e. report/failed, report/author @ report/assay_type, report/patient_info/Study, report/patient_info/Primary cancer, report/patient_info/Genetic Sex @ report/patient_info/Site of biopsy/surgery", '\n')
                    query = input ('Filter Multiple: ')
                    return query
               elif filter_type == 'e' or filter_type == 'equal': 
                    print("  <enter filters like tuple within brackets> <access nested keys w forwardslash> <separate key/value and different views w comma> ", '\n',
                    " i.e. (report/failed, true) ", '\n',
                    " i.e. (report/failed, true), (report/author, Felix Beaudry), (report/oncogenic_somatic_CNVs/Total variants, 35), (report/patient_info/Site of biopsy/surgery, Liver)", '\n')
                    query = input('Equal: ')  
                    return query
               elif  filter_type == 'l' or filter_type == 'less' or filter_type == 'g' or filter_type == 'great':
                    print("<enter filters like tuple within brackets> <access nested keys w forwardslash> <separate key/value and different views w comma> ", '\n',
                    " i.e. (report/oncogenic_somatic_CNVs/Total variants, 35) ", '\n',
                    " i.e. (report/oncogenic_somatic_CNVs/Total variants, 35) , (report/sample_info_and_quality/Estimated Ploidy, 3.5)")
                    if filter_type == 'l' or filter_type == 'less': query = input('Less: ')  
                    if filter_type == 'g' or filter_type == 'great': query = input('Great: ')  
                    return query
          else: 
               logging.error('Invalid filter type')
          return 

if __name__ == "__main__":
     Design().SetUp()
