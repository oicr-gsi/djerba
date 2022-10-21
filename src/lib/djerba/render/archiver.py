"""Archive files to a given directory for later reference"""

import hashlib
import json
import logging
import shutil
import os
import re

import djerba.util.constants as constants
import djerba.render.constants as render_constants
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.validator import path_validator

from djerba.render.database import Database 


class archiver(logger):
    """Archive the report JSON to a directory, with hashing to avoid overwrites"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.converter = converter(log_level, log_path)
        self.validator = path_validator(log_level, log_path)
        self.logger.info('Initializing archiver object from archiver.py')

    def read_and_preprocess(self, data_path):
        # read the JSON and convert image paths to base64 blobs
        self.logger.debug("Reading data path {0}".format(data_path))
        with open(data_path) as data_file:
            data_string = data_file.read()
        data = json.loads(data_string)
        # shorter key names
        rep = constants.REPORT
        tmb = render_constants.TMB_PLOT
        vaf = render_constants.VAF_PLOT
        logo = render_constants.OICR_LOGO
        # convert image paths (if any, they may already be base64)
        data[rep][logo] = self.converter.convert_png(data[rep][logo], 'OICR logo')
        data[rep][tmb] = self.converter.convert_svg(data[rep][tmb], 'TMB plot')
        data[rep][vaf] = self.converter.convert_svg(data[rep][vaf], 'VAF plot')
        return json.dumps(data)

    def db(self, data_path):
        self.logger.info('run method from archiver class STARTING')
        data_string = self.read_and_preprocess(data_path)
        ###data_path is path to json file
        json_doc = data_path
        db = Database()
        with open(json_doc) as f:
            data_string = f.read()
            data = json.loads(data_string)
            #print(data)
        data_path = data_path.split("/")
        data_path.pop()
        folder = "/".join(data_path)
        db.UploadFile(data_path)


        # self.logger.info('Adds suffix for db versioning')
        # newVersion = False
        # data["_id"] = data["report"]["patient_info"]["Report ID"]+'-db1'
        # self.logger.info('Add suffix for first db version')
        # while newVersion == False:
        #     currdbid = data["_id"]
        #     os.remove(json_doc)
        #     with open(json_doc, 'w') as f: json.dump(data, f)
        #     status = db.UploadFile(folder) #assumes 1 file so only 1 status code
        #     if status == 201:
        #         self.logger.info('Succesful upload to db: {}'.format(data["_id"]))
        #         newVersion = True
        #     elif status == 409:
        #         self.logger.debug('Document update conflict')
        #         temp = data["_id"]
        #         pre,suff = temp.split("db")
        #         suff = int(suff) + 1
        #         newdbid = str(suff)
        #         newdbid = pre+'db'+newdbid
        #         data["_id"] = newdbid
        # self.logger.info('run method from archiver class FINISHED')
        print()
        print(status)
        print()
        return status


    '''makes temp archive folder and increments DB Versioning'''
    def run(self, data_path, archive_dir, patient_id):
        self.logger.info('run method from archiver class STARTING')
        data_string = self.read_and_preprocess(data_path)
        m = hashlib.md5()
        m.update(data_string.encode(constants.TEXT_ENCODING))
        md5sum = m.hexdigest()
        # construct the output path, creating directories if necessary
        self.validator.validate_output_dir(archive_dir)
        archive_dir = os.path.realpath(archive_dir)
        out_dir_0 = os.path.join(archive_dir, patient_id)
        if not os.path.exists(out_dir_0):
            os.mkdir(out_dir_0)
        out_dir_1 = os.path.join(out_dir_0, md5sum)
        out_path = None
        # if output was not previously written, write it now
        if not os.path.exists(out_dir_1):
            os.mkdir(out_dir_1)
        suffix = md5sum[0:8]
        out_path = os.path.join(out_dir_1, "{0}_{1}.json".format(patient_id, suffix))
        if os.path.exists(out_path):
            msg = "Output path {0} exists; ".format(out_path)+\
                  "an identical file has already been archived; not writing to archive"
            print(msg)
            self.logger.debug(msg)
        else:
            with open(out_path, 'w') as out_file:
                out_file.write(data_string)
            self.logger.debug("Archived JSON to {0}".format(out_path))

        db = Database()
        if archive_dir.strip()[-1] != '/': archive_dir += '/'
        folder = archive_dir+patient_id
        files = []
        dirs = []
        findjson = folder
        for (findfolder, dir_names, file_names) in os.walk(findjson): 
            files.extend(file_names)
            dirs.extend(dir_names)
        for i in range(len(files)):
            if files[i][-5:] == '.json': 
                json_doc = dirs[i]+'/'+files[i]
        json_doc = folder+'/'+json_doc
        f = open(json_doc)
        data = json.load(f)
        self.logger.info('Adds suffix for db versioning')
        newVersion = False
        data["_id"] = data["report"]["patient_info"]["Report ID"]+'-db1'
        self.logger.info('Add suffix for first db version')
        while newVersion == False:
            currdbid = data["_id"]
            os.remove(json_doc)
            with open(json_doc, 'w') as f: json.dump(data, f)
            status = db.UploadFolder(folder) #assumes 1 file so only 1 status code
            if status == 201:
                self.logger.info('Succesful upload to db: {}'.format(data["_id"]))
                newVersion = True
            elif status == 409:
                self.logger.debug('Document update conflict')
                temp = data["_id"]
                pre,suff = temp.split("db")
                suff = int(suff) + 1
                newdbid = str(suff)
                newdbid = pre+'db'+newdbid
                data["_id"] = newdbid
        if os.path.exists(folder): #delete temp archive folder that was just created
            shutil.rmtree(folder)
            self.logger.debug(f'Temp Path has been Removed: {folder}')
            self.logger.info(f'Removed Patient ID {patient_id} from archive dir: {archive_dir}')
        self.logger.info('run method from archiver class FINISHED')
        return out_path

    