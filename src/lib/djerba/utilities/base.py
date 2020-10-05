"""Base class with some general-purpose methods"""

import logging
import os
import sys

class base:

    def get_log_level(self, debug=False, verbose=False):
        log_level = logging.WARN
        if debug:
            log_level = logging.DEBUG
        elif verbose:
            log_level = logging.INFO
        return log_level
    
    def get_logger(self, log_level=logging.WARN, name=None, log_path=None):
        """Create a Logger object with class identifier, log level, optional output path"""
        if name == None: name = "%s.%s" % (__name__, type(self))
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        if len(logger.handlers) > 0: # remove duplicate handlers from previous get_logger() calls
            logger.handlers.clear()
        handler = None
        if log_path==None:
            handler = logging.StreamHandler()
        else:
            dir_path = os.path.abspath(os.path.join(log_path, os.pardir))
            valid = True
            if not os.path.exists(dir_path):
                sys.stderr.write("ERROR: Log directory %s does not exist.\n" % dir_path)
                valid = False
            elif not os.path.isdir(dir_path):
                sys.stderr.write("ERROR: Log destination %s is not a directory.\n" % dir_path)
                valid = False
            elif not os.access(dir_path, os.W_OK):
                sys.stderr.write("ERROR: Log directory %s is not writable.\n" % dir_path)
                valid = False
            if not valid: sys.exit(1)
            handler = logging.FileHandler(log_path)
        handler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s',
                                      datefmt='%Y-%m-%d_%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

