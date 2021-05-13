"""
Classes to contain gene and sample attributes

Includes methods to update attributes, check consistency, and validate against schema
"""

class container:
    """Parent class for gene-level and sample-level attribute containers"""

    GENE_METRICS_KEY = 'gene_metrics'
    GENE_NAME_KEY = 'Gene'
    ITEMS_KEY = 'items'
    PROPERTIES_KEY = 'properties'
    SAMPLE_INFO_KEY = 'sample_info'
    SAMPLE_ID_KEY = 'SAMPLE_ID'

    def __init__(self, attributes, schema):
        """
        Subclasses should call the parent constructor and set self.name_key
        """
        self.attributes = attributes
        self.permitted_attributes = self._get_permitted_attributes(schema)
        self.name_key = None
        # Check that attribute names are permitted in the schema
        # We check against the full schema, as a final step in reader.get_output()
        for key in self.attributes.keys():
            if not key in self.permitted_attributes:
                msg = "Key '%s' is not permitted by schema" % str(key)
                msg += "\nPermitted attributes: "+str(sorted(list(self.permitted_attributes)))
                raise ValueError(msg)                

    def _get_permitted_attributes(self, schema):
        """Override in child classes"""
        return {}

    def has_same_attribute_names(self, other):
        """Check for congruent attributes with another container"""
        return self.get_attribute_name_set() == other.get_attribute_name_set()

    def is_complete(self):
        """Check if all attributes permitted by the schema have been specified"""
        return self.get_attribute_name_set() == self.permitted_attributes

    def get_attribute_name_set(self):
        return set(self.attributes.keys())

    def get_attribute(self, key):
        return self.attributes.get(key)

    def get_attributes(self):
        return self.attributes

    def get_name(self):
        return self.attributes.get(self.name_key)

    def update(self, other):
        """
        Update with another container; check validity against schema, and consistency of values
        """
        for key in other.get_attribute_name_set():
            if key in self.permitted_attributes:
                if key in self.attributes:
                    if self.attributes[key] != other.get_attribute(key):
                        msg = "Inconsistent values for attribute %s: " % key +\
                            "Expected '%s'," % str(self.attributes[key]) +\
                            "found '%s'" % str(other.get_attribute(key))
                        raise ValueError(msg)
                else:
                    self.attributes[key] = other.get_attribute(key)
            else:
                # check here as well as __init__ in case eg. we are updating wtih the wrong subclass
                msg = "Key '%s' is not permitted by schema" % str(key)
                raise ValueError(msg)

class gene(container):
    """
    Class to represent a gene and contain relevant metrics
    """

    def __init__(self, attributes, schema):
        super().__init__(attributes, schema)
        self.name_key = self.GENE_NAME_KEY
    
    def _get_permitted_attributes(self, schema):
        try:
            permitted = set(
                schema[self.PROPERTIES_KEY][self.GENE_METRICS_KEY][self.ITEMS_KEY][self.PROPERTIES_KEY].keys()
            )
        except KeyError as err:
            raise RuntimeError('Bad schema format; could not find expected keys') from err
        return permitted

class sample(container):

    """
    Class to represent a sample and contain sample-level attributes
    """

    def __init__(self, attributes, schema):
        super().__init__(attributes, schema)
        self.name_key = self.SAMPLE_ID_KEY
    
    def _get_permitted_attributes(self, schema):
        try:
            permitted = set(
                schema[self.PROPERTIES_KEY][self.SAMPLE_INFO_KEY][self.PROPERTIES_KEY].keys()
            )
        except KeyError as err:
            raise RuntimeError('Bad schema format; could not find expected keys') from err
        return permitted

