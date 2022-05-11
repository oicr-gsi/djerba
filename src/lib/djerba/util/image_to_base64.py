"""Convenience methods to convert image files to base64 text blobs"""

import base64
import djerba.util.constants as constants

def convert(image_path, image_type):
    if image_type not in ['jpeg', 'png']:
        raise RuntimeError("Unsupported image type: {0}".format(image_type))
    with open(image_path, 'rb') as image_file:
        image_string = base64.b64encode(image_file.read()).decode(constants.TEXT_ENCODING)
    image_json = 'data:image/{0};base64,{1}'.format(image_type, image_string)
    return image_json

def convert_jpeg(in_path):
    return convert(in_path, 'jpeg')

def convert_png(in_path):
    return convert(in_path, 'png')
