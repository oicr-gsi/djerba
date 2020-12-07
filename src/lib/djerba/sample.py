"""Sample class; thin wrapper for a dictionary containing sample attributes"""

import logging
from djerba.utilities import constants
from djerba.utilities.base import base

class sample(base):

    """
    Sample for rShiny or cBioPortal reports. Input is a simple dictionary of attributes 
    (key/value pairs) for the sample. The only required attribute is SAMPLE_ID."""
    
    def __init__(self, attributes, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, "%s.%s" % (__name__, type(self).__name__), log_path)
        self.sample_id = attributes.get(constants.SAMPLE_ID_KEY)
        if self.sample_id == None:
            msg = "Missing required input key %s" % constants.SAMPLE_ID_KEY
            self.logger.error(msg)
            raise ValueError(msg)
        self.attributes = attributes

    def get(self, key):
        return self.attributes.get(key)
        
    def get_attributes(self):
        return self.attributes

    def get_id(self):
        return self.sample_id

    def update_attributes(self, new_attributes):
        shared_keys = set(self.attributes.keys()).intersection(set(new_attributes.keys()))
        if len(shared_keys)>0:
            # found shared keys other than 'Gene': issue a warning
            key_string = ", ".join(sorted([str(x) for x in shared_keys]))
            msg = "Existing attribute values will be overwritten for keys: %s" % key_string
            self.logger.warning(msg)
        self.attributes.update(new_attributes)
