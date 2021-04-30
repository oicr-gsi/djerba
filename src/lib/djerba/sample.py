"""Sample class; wrapper for a dictionary containing sample attributes"""

import logging
from djerba.utilities import constants
from djerba.utilities.base import base

class sample(base):

    """
    Sample for rShiny or cBioPortal reports. Input is a simple dictionary of attributes 
    (key/value pairs) for the sample. The only required attribute is SAMPLE_ID.
    """
    
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

    def update_attributes(self, new_attributes, overwrite=False):
        shared_set = set(self.attributes.keys()).intersection(set(new_attributes.keys()))
        shared_set.discard(constants.GENE_KEY)
        # overwriting null sample attributes is permitted; filter out null values
        shared = [x for x in shared_set if not self.is_null(self.attributes.get(x))]
        if overwrite==False and len(shared)>0:
            key_string = ", ".join(sorted([str(x) for x in shared]))
            msg = "Multiple non-null sample attribute values found for keys: [%s]. " % key_string +\
                  "Overwrite mode is not in effect."
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.attributes.update(new_attributes)
