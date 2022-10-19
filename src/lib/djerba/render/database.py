"""Interface with a CouchDB instance for JSON report documents"""

import logging
from djerba.util.logger import logger
#from logger import logger

from djerba.render.addclasslog import Add 
#from addclasslog import Add

class Database(logger):
#class database():
    """Class to communicate with CouchDB via the API, eg. using HTTP GET/POST statements"""

    def __init__(self, log_level=logging.DEBUG, log_path='/.mounts/labs/gsiprojects/gsi/gsiusers/ltoy/djerba/src/lib/djerba/render/test.log'):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Initializing Djerba database object")
    
    def Upload(self,folder):
        self.logger.info('Database class Upload method STARTING')
        instance = Add()
        folder = folder
        status = instance.AddFolder(folder)
      
        self.logger.info('printed to terminal for user the status of upload - assume 1 DOC!')
        self.logger.info('Database class Upload method FINISHED')
        return status


# instance = Database()
# answer = instance.Upload()

