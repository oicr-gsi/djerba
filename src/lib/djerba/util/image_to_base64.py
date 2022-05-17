"""Convenience methods to convert image files to base64 text blobs for JSON output"""

import base64
import logging
import djerba.util.constants as constants
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class converter(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)

    def convert(self, image_path, image_type):
        if image_type not in ['jpeg', 'png']:
            msg = "Unsupported image type: {0}".format(image_type)
            self.logger.error(msg)
            raise RuntimeError(msg)
        self.validator.validate_input_file(image_path)
        with open(image_path, 'rb') as image_file:
            image_string = base64.b64encode(image_file.read()).decode(constants.TEXT_ENCODING)
        image_json = 'data:image/{0};base64,{1}'.format(image_type, image_string)
        return image_json

    def convert_jpeg(self, in_path):
        return self.convert(in_path, 'jpeg')

    def convert_png(self, in_path):
        return self.convert(in_path, 'png')
