import posixpath
import argparse
import logging
import json
import csv
import os

class Process():
    def __init__(self, level=logging.INFO, log_path=None, filename=__name__):
        self.level = level
        self.filename = filename
        self.log_path = log_path
        if log_path != None:
            file_path = join(self.log_path, self.filename)
            file_path += '.log'
        else: file_path = None
        logging.basicConfig(level=level, filename=file_path, format=f'%(asctime)s:%(filename)s:%(levelname)s: %(message)s', datefmt='%Y-%m-%d_%H:%M:%S')
    
    def gene_type_study(self, ptype, json_path, out_dir, out_name):
        with open(json_path) as json_file:
            data = json.load(json_file)

        if out_name == None:
            out_name = json_path.split("/")
            out_name= out_name[-1].replace(".json","")
            out_name += '_processed'
        else: out_name == out_name 
        
        if out_dir == None:
            run_path = os.path.realpath(__file__)
            base = run_path.split("/")
            base = base[:-1]
            base = "/".join(base)
            if os.path.exists(posixpath.join(base, 'extract')) == False:
                os.mkdir(posixpath.join(base, 'extract'))
                logging.debug(f"Created output directory {posixpath.join(base, 'extract')}")
            out_path = posixpath.join(base, 'extract', f"{out_name}.csv")
        else: out_path = posixpath.join(out_dir, f"{out_name}.csv")

        with open(out_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            if ptype == 'small': header = ["_id", "Gene", "Type", "Study", "TMB"]
            if ptype == 'onco': header = ["_id", "Gene", "Alteration", "Study", "TMB"]
            writer.writerow(header)
            for report in data:
                py_dict = report
                #print(type(py_dict), len(py_dict))
                report_id = py_dict["_id"]
                body_list = py_dict["Body"]
                study = py_dict["Study"]
                tmb = py_dict["Tumour Mutation Burden"]
                if study == 'PASS-01': study = 'PASS01'
                if study == 'CYP': study = 'CYPRESS'
                #print(len(body_list), type(body_list))
                for entry in body_list:
                    info_dict = entry
                    gene = info_dict["Gene"]
                    if ptype == 'small': mutype = info_dict["Type"]
                    if ptype == 'onco': mutype = info_dict["Alteration"]
                    #print(report_id, gene, mutation_type)
                    new_row = [report_id, gene, mutype, study, tmb]
                    writer.writerow(new_row)
            csv_file.close()
        logging.info(f'file path {out_path}')
        return out_path
    
    def small_mutations_and_indels(self, json_path):
        json_path = json_path
        with open(json_path) as json_file:
            data = json.load(json_file)

        out_name = json_path.split("/")
        out_name= out_name[-1].replace(".json","")
        run_path = os.path.realpath(__file__)
        base = run_path.split("/")
        base = base[:-1]
        base = "/".join(base)

        if os.path.exists(posixpath.join(base, 'extract')) == False:
            os.mkdir(posixpath.join(base, 'extract'))
            logging.debug(f"Created output directory {posixpath.join(base, 'extract')}")
        out_path = posixpath.join(base, 'extract', f"{out_name}_processed.csv")

        with open(out_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            header = ["_id", "Gene", "Type", "Study"]
            writer.writerow(header)
            for report in data:
                py_dict = report
                #print(type(py_dict), len(py_dict))
                report_id = py_dict["_id"]
                body_list = py_dict["Body"]
                study = py_dict["Study"]
                if study == 'PASS-01': study = 'PASS01'
                #print(len(body_list), type(body_list))
                for entry in body_list:
                    info_dict = entry
                    gene = info_dict["Gene"]
                    mutation_type = info_dict["Type"]
                    #print(report_id, gene, mutation_type)
                    new_row = [report_id, gene, mutation_type, study]
                    writer.writerow(new_row)
            csv_file.close()
        logging.info(f'file path {out_path}')
        return out_path

    def oncogenic_somatic_CNVs(self, json_path):
        json_path = json_path
        with open(json_path) as json_file:
            data = json.load(json_file)

        out_name = json_path.split("/")
        out_name= out_name[-1].replace(".json","")
        run_path = os.path.realpath(__file__)
        base = run_path.split("/")
        base = base[:-1]
        base = "/".join(base)
        
        if os.path.exists(posixpath.join(base, 'extract')) == False:
            os.mkdir(posixpath.join(base, 'extract'))
            logging.debug(f"Created output directory {posixpath.join(base, 'extract')}")
        out_path = posixpath.join(base, 'extract', f"{out_name}_processed.csv")

        with open(out_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            header = ["_id", "Gene", "Alteration", "Study"]
            writer.writerow(header)
            for report in data:
                py_dict = report
                #print(type(py_dict), len(py_dict))
                report_id = py_dict["_id"]
                body_list = py_dict["Body"]
                study = py_dict["Study"]
                if study == 'PASS-01': study = 'PASS01'
                #print(len(body_list), type(body_list))
                for entry in body_list:
                    info_dict = entry
                    gene = info_dict["Gene"]
                    alteration_type = info_dict["Alteration"]
                    #print(report_id, gene, mutation_type)
                    new_row = [report_id, gene, alteration_type, study]
                    writer.writerow(new_row)
            csv_file.close()
        logging.info(f'file path {out_path}')
        return out_path

    def SetUp(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('process', help='small or onco')#, type=str, action="store", dest="filter", required=True)
        parser.add_argument("-j", "--json", help='input json from multi filter, wrap in quotes ""', action="store", type=str, dest="json", default=None)
        parser.add_argument("-d", "--dir", help="output directory, default is extract dir at file path", action="store", type=str, dest="dir", default=None)
        parser.add_argument("-n", "--name", help="output csv name default to input_processed", action="store", type=str, dest="name", default=None)
        # parser.add_argument("-p", "--print", help="print to terminal", action="store_true", dest="cmdprint", default=False)
        args = parser.parse_args()
        if args.process != 'onco' and args.process != 'small':
            logging.error('invalid process chosen')
            return
        if args.json == None: 
            logging.error('path to input json required')
            return
        if args.dir != None and os.path.isdir(args.dir) == False:
            logging.error('output path is not a directory')
            return
        ptype = args.process
        json_path = args.json
        out_dir = args.dir
        out_name = args.name
        self.gene_type_study(ptype, json_path, out_dir, out_name)
        return

if __name__ == "__main__":
    Process().SetUp()
    # #multi filter of report/patient_info/Study, report/small_mutations_and_indels/Body 
    # json_path = '/home/ltoy/Desktop/couch/extract/small_type_study_Study&Body.json'
    # Graph().small_mutations_and_indels(json_path)
    # #multi filter of report/patient_info/Study, report/oncogenic_somatic_CNVs/Body
    # json_path = '/home/ltoy/Desktop/couch/extract/onco_type_study_Study&Body.json'
    # Graph().oncogenic_somatic_CNVs(json_path)
