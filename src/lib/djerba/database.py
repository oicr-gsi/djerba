"""Interface with a CouchDB instance for JSON report documents"""

import logging

from djerba.util.logger import logger

class database(logger):

    """Class to communicate with CouchDB via the API, eg. using HTTP GET/POST statements"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.info("Initializing Djerba database object")

    def upload(self, document):
        # placeholder; TODO add the uploading functionality
        self.logger.info("Upload")
