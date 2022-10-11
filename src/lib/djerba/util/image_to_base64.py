"""Convenience methods to convert image files to base64 text blobs for JSON output"""

import base64
import logging
import re
import djerba.util.constants as constants
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class converter(logger):

    DEFAULT_DESC = 'image'
    JPEG = 'jpeg'
    PNG = 'png'
    SVG = 'svg+xml'
    SUPPORTED = [JPEG, PNG, SVG]

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)

    def convert(self, image_input, image_type, description=DEFAULT_DESC):
        if image_type not in self.SUPPORTED:
            msg = "Image type '{0}' not in supported types {1}".format(image_type, self.SUPPORTED)
            self.logger.error(msg)
            raise RuntimeError(msg)
        if self.is_convertible(image_input, description):
            with open(image_input, 'rb') as image_file:
                image_string = base64.b64encode(image_file.read()).decode(constants.TEXT_ENCODING)
            image_json = 'data:image/{0};base64,{1}'.format(image_type, image_string)
            msg = "Converted {0} {1} {2} to base64".format(image_type, description, image_input)
            self.logger.debug(msg)
        else:
            image_json = image_input
            msg = "Omitting base64 conversion; {0} ".format(description)+\
                  "input (truncated to 50 characters): {0}".format(image_input[0:50])
            self.logger.debug(msg)
        return image_json

    def convert_jpeg(self, in_path, description=DEFAULT_DESC):
        return self.convert(in_path, self.JPEG, description)

    def convert_png(self, in_path, description=DEFAULT_DESC):
        return self.convert(in_path, self.PNG, description)

    def convert_svg(self, in_path, description=DEFAULT_DESC):
        return self.convert(in_path, self.SVG, description)

    def is_convertible(self, arg, description=DEFAULT_DESC):
        """Argument may be a path or already a base64 blob; check if it can be converted to base64"""
        convertible = True
        if re.match('data:image', arg):
            self.logger.debug(description+" is already encoded; invalid for base64 conversion")
            convertible = False
        elif not self.validator.validate_input_file(arg):
            msg = "{0} argument {1} is not a valid input file; ".format(description, arg)+\
                  "invalid for base64 conversion"
            self.logger.warn(msg)
            convertible = False
        else:
            msg = "{0} argument {1} is a valid target for base64 conversion".format(description, arg)
            self.logger.debug(msg)
        return convertible
