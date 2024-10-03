"""Base class with logging functions"""

import logging
import os
import sys

class logger:

    """Logging functions; inherit from this class to enable logging"""

    def __init__(self):
        pass

    @staticmethod
    def get_args_log_level(args):
        # the 'silent' attribute is optional; used in mini-Djerba
        if not hasattr(args, 'silent'):
            args.silent = False
        return logger.get_log_level(args.debug, args.verbose, args.quiet, args.silent)

    @staticmethod
    def get_log_level(debug=False, verbose=False, quiet=False, silent=False):
        log_level = logging.WARN
        if debug:
            log_level = logging.DEBUG
        elif verbose:
            log_level = logging.INFO
        elif quiet:
            log_level = logging.ERROR
        elif silent:
            log_level = logging.CRITICAL + 10
        return log_level
    
    def get_logger(self, log_level=logging.WARN, name=None, log_path=None):
        """Create a Logger object with class identifier, log level, optional output path"""
        log_name = name if name else __name__ # __name__ is djerba.util.logger
        logger = logging.getLogger(log_name)
        logger.setLevel(log_level)
        if len(logger.handlers) > 0: # remove duplicate handlers from previous get_logger() calls
            for handler in logger.handlers:
                handler.close()
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
