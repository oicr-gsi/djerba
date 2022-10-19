"""
Render Djerba results in HTML and PDF format
"""

import json
import logging
import shutil #removes directory
import os
import pdfkit
import traceback
#
import requests 
import configparser
from pathlib import Path
#
from mako.template import Template
from mako.lookup import TemplateLookup

import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.render.archiver import archiver
#from archiver import archiver
#
from djerba.render.database import Database
#from database import Database
#
from djerba.util.logger import logger
#from logger import logger

class html_renderer(logger):

    def __init__(self, log_level=logging.DEBUG, log_path='/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/test.log'):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'html'
        ))
        # strict_undefined=True provides an informative error for missing variables in JSON
        # see https://docs.makotemplates.org/en/latest/runtime.html#context-variables
        report_lookup = TemplateLookup(directories=[html_dir,], strict_undefined=True)
        self.template = report_lookup.get_template("clinical_report_template.html")
        
        self.logger.info('Initializing html_renderer object')

    def run(self, in_path, out_path, archive=True):
        self.logger.info('run method of html_renderer class STARTING from render.py')
        with open(in_path) as in_file:
            data = json.loads(in_file.read())
            args = data.get(constants.REPORT)
            config = data.get(constants.SUPPLEMENTARY).get(constants.CONFIG)
        with open(out_path, 'w') as out_file:
            try:
                html = self.template.render(**args)
            except Exception as err:
                msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
                self.logger.error(msg)
                trace = ''.join(traceback.format_tb(err.__traceback__))
                self.logger.error('Traceback: {0}'.format(trace))
                raise
            print(html, file=out_file)
        if archive:
            self.logger.info("Finding archive parameters for {0}".format(out_path))
            try:
                archive_dir = config[ini.SETTINGS][ini.ARCHIVE_DIR]
            except KeyError:
                self.logger.warn("Archive directory not found in config")
                archive_dir = None
            try:
                patient_id = config[ini.DISCOVERED][ini.PATIENT_ID]
            except KeyError:
                patient_id = 'Unknown'
                msg = "Patient ID not found in config, falling back to '{0}'".format(patient_id)
                self.logger.warn(msg)
            if archive_dir:
                split = in_path.split("/")
                split.pop()
                split = "/".join(split)
                archive_dir = split ###CHANGES DF ARCHIVE_DIR TO INPUT DIR, SO NO INTERMEDIATE WRITE IF DELETED AFTER BELOW
                archive_args = [in_path, archive_dir, patient_id]
                self.logger.info("Archiving {0} to {1} with ID '{2}'".format(*archive_args))
                archiver(self.log_level, self.log_path).run(*archive_args)

                db = Database()
                if archive_dir.strip()[-1] != '/': archive_dir += '/'
                folder = archive_dir+patient_id
                
                #check for doc_id existance in db, increment report_version otherwise to allow upload
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
                #find_doc = 'http://10.30.133.78:5984/_utils/#database/djerba_dev01/'+report_id  #need change url later
                #existance = requests.head(find_doc)
                
                #ADDS SUFFIX TO REPORT ID I.E. -db1 FOR VERSIONING IN DB
                newVersion = False
                data["_id"] = data["report"]["patient_info"]["Report ID"]+'-db1'
                #data["report"]["patient_info"]["Report ID"] = data["report"]["patient_info"]["Report ID"]+'-db1'
                self.logger.info('Add suffix for first dv version')
                while newVersion == False:
                    currdbid = data["_id"]
                    print(currdbid)
                    #data["_id"] = data["report"]["patient_info"]["Report ID"]+'-db1'
                    #data["report"]["patient_info"]["Report ID"] = data["report"]["patient_info"]["Report ID"]+'-db1'
                    os.remove(json_doc)
                    with open(json_doc, 'w') as f:
                        json.dump(data, f)
                    
                    status = db.Upload(folder) #assumes 1 file so only 1 status code
                    #print(data["report"]["patient_info"]["Report ID"], data["supplementary"]["config"]["inputs"]["report_version"])  
                    if status == 201:
                        self.logger.info('Succesful upload to db')
                        #print(data["report"]["patient_info"]["Report ID"], data["supplementary"]["config"]["inputs"]["report_version"])  
                        newVersion = True
                    elif status == 409:
                        self.logger.error('Document update conflict')
                        #oldv = 'v'+str(data["supplementary"]["config"]["inputs"]["report_version"])
                        #data["supplementary"]["config"]["inputs"]["report_version"] += 1
                        #newv = 'v'+str(data["supplementary"]["config"]["inputs"]["report_version"]) 
                        #self.logger.info("Incremented report_version") #NOT DO
                        
                        #temp = data["report"]["patient_info"]["Report ID"] 
                        temp = data["_id"]
                        print(temp)
                        pre,suff = temp.split("db")
                        suff = int(suff) + 1
                        newdbid = str(suff)
                        newdbid = pre+'db'+newdbid
                        data["_id"] = newdbid
                        print(data["_id"  ])
                        
                        #data["report"]["patient_info"]["Report ID"] = newdbid
    
                        #oldid = data["report"]["patient_info"]["Report ID"] 
                        #data["report"]["patient_info"]["Report ID"] = data["report"]["patient_info"]["Report ID"].replace(oldv,newv)
                        #self.logger.info("Increment Report ID")

                        # os.remove(json_doc)
                        # with open(json_doc, 'w') as f:
                        #     json.dump(data, f)
                        # print(data["report"]["patient_info"]["Report ID"], data["supplementary"]["config"]["inputs"]["report_version"])
                        
                #print(folder)
                if os.path.exists(folder): #delete temp archive folder that was just created
                    shutil.rmtree(folder)
                    print(f'Existing Path has been Removed: {folder}')
                    self.logger.info(f'Removed Patient ID {patient_id} from archive dir: {archive_dir}')

                #RENAMES HTML - NOT NEEDED IF VERSIONING DOESN'T CHANGE
                # for f in os.listdir(split):
                #     filename = os.fsdecode(f)
                #     #if filename.endswith(".html"):
                #     if filename == oldid+'_report.html':
                #         newname = filename.replace(oldv, newv)
                #         print('newname: ', newname)
                #         print('filename: ', filename)
                #         # newname = filename.replace(oldv, newv)
                #         # print(filename, newname)
                #         os.system(f"mv {split}/{filename} {split}/{newname}")
    
                self.logger.debug("Archiving done")
            else:
                self.logger.warn("No archive directory; omitting archiving")

        else:
            self.logger.info("Archive operation not requested; omitting archiving")
        
        self.logger.info("Completed HTML rendering of {0} to {1}".format(in_path, out_path))

        self.logger.info('run method of html_renderer class FINISHED from render.py')

class pdf_renderer(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)

    # Running the PDF renderer requires the wkhtmltopdf binary on the PATH
    # This can be done by loading the wkhtmltopdf environment module:
    # https://gitlab.oicr.on.ca/ResearchIT/modulator/-/blob/master/code/gsi/70_wkhtmltopdf.yaml

    # Current implementation runs with javascript disabled
    # If javascript is enabled, PDF rendering attempts a callout to https://mathjax.rstudio.com
    # With Internet access, this works; otherwise, it times out after ~4 minutes and PDF rendering completes
    # But rendering without Javascript runs successfully with no apparent difference in output
    # So it is disabled, to allow fast running on a machine without Internet (eg. cluster node)
    # See https://github.com/wkhtmltopdf/wkhtmltopdf/issues/4506
    # An alternative solution would be changing the HTML generation to omit unnecessary Javascript

    def run(self, html_path, pdf_path, footer_text=None, footer=True):
        """Render HTML to PDF"""
        # create options, which are arguments to wkhtmltopdf for footer generation
        # the 'quiet' option suppresses chatter to STDOUT
        self.logger.info('Writing PDF to {0}'.format(pdf_path))
        if footer:
            if footer_text:
                self.logger.info("Including footer text for CGI clinical report")
                options = {
                    'footer-right': '[page] of [topage]',
                    'footer-center': footer_text,
                    'quiet': '',
                    'disable-javascript': ''
                }
            else:
                self.logger.info("Including page numbers but no additional footer text")
                options = {
                    'footer-right': '[page] of [topage]',
                    'quiet': '',
                    'disable-javascript': ''
                }
        else:
            self.logger.info("Omitting PDF footer")
            options = {
                'quiet': '',
                'disable-javascript': ''
            }
        try:
            pdfkit.from_file(html_path, pdf_path, options = options)
        except Exception as err:
            msg = "Unexpected error of type {0} in PDF rendering: {0}".format(type(err).__name__, err)
            self.logger.error(msg)
            trace = ''.join(traceback.format_tb(err.__traceback__))
            self.logger.error('Traceback: {0}'.format(trace))
            raise
        self.logger.info('Finished writing PDF')



##html mode - input json document produced by extract, write html report, optionally write PDF report
##requires input json and output html, otherwise specify directory which searches for these 
# r = html_renderer()
# injson = '/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/lauren_djerba_report.json'
# outhtml = '/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/lauren_djerba_report.html'
# r.run(injson,outhtml)

# db = Database()
# upload = db.Upload()
