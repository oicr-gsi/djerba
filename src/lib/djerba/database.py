"""Interface with a CouchDB instance for JSON report documents"""

import logging
import addclass 

from djerba.util.logger import logger
from addclass import Add 

class database(logger):
#class database():
    """Class to communicate with CouchDB via the API, eg. using HTTP GET/POST statements"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Initializing Djerba database object")
    
    #def __init__(self):
    #    pass

    def upload(self):
        # placeholder; TODO add the uploading functionality

        instance = Add()
        folder_path = instance.AddFolder()
        print(folder_path)

instance = database()
answer = instance.upload()

