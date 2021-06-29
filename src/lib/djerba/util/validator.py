"""Validate inputs, eg. by checking filesystem status"""

import os

class validator:

    """Check that inputs are valid; if not, raise an error"""

    # TODO instead of raising an error, could log outcome and return boolean

    def __init__(self):
        pass        

    def validate_input_dir(self, path):
        """Confirm an input directory exists and is readable"""
        valid = False
        if not os.path.exists(path):
            raise OSError("Input path %s does not exist" % path)
        elif not os.path.isdir(path):
            raise OSError("Input path %s is not a directory" % path)
        elif not os.access(path, os.R_OK):
            raise OSError("Input path %s is not readable" % path)
        else:
            valid = True
        return valid
    
    def validate_input_file(self, path):
        """Confirm an input file exists and is readable"""
        valid = False
        if not os.path.exists(path):
            raise OSError("Input path %s does not exist" % path)
        elif not os.path.isfile(path):
            raise OSError("Input path %s is not a file" % path)
        elif not os.access(path, os.R_OK):
            raise OSError("Input path %s is not readable" % path)
        else:
            valid = True
        return valid
        
    def validate_output_dir(self, path):
        """Confirm an output directory exists and is writable"""
        valid = False
        if not os.path.exists(path):
            raise OSError("Output path %s does not exist" % path)
        elif not os.path.isdir(path):
            raise OSError("Output path %s is not a directory" % path)
        elif not os.access(path, os.W_OK):
            raise OSError("Output path %s is not writable" % path)
        else:
            valid = True
        return valid

    def validate_output_file(self, path):
        """Confirm an output file can be written"""
        valid = False
        if os.path.isdir(path):
            raise OSError("Output file %s cannot be a directory" % path)
        elif os.path.exists(path) and not os.access(path, os.W_OK):
            raise OSError("Output file %s exists and is not writable" % path)
        else:
            parent = os.path.dirname(os.path.realpath(path))
            try:
                valid = self.validate_output_dir(parent)
            except OSError as err:
                raise OSError("Parent directory of output path %s is not valid" % path) from err
        return valid
    
    def validate_present(self, config, section, param):
        # throws a KeyError if param is missing; TODO informative error message
        return config[section][param]
