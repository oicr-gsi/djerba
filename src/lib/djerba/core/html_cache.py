"""
Class to cache/update HTML in JSON
Not to be confused with the OncoKB cache!
"""

from xml.dom import minidom
from xml.parsers.expat import ExpatError
import base64
import gzip
import json
import logging
import re
import djerba.core.constants as cc
from djerba.util.logger import logger

class html_cache(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def decode_from_base64(self, encoded_string):
        return gzip.decompress(base64.b64decode(encoded_string)).decode(cc.TEXT_ENCODING)

    def encode_to_base64(self, string_to_encode):
        return base64.b64encode(gzip.compress(string_to_encode.encode(cc.TEXT_ENCODING)))

    def parse_name_from_separator(self, separator_line):
        # attempt to parse the HTML separator line
        separator_line = separator_line.strip()
        try:
            doc = minidom.parseString(separator_line)
        except ExpatError as err:
            msg = "Failed to parse component name in HTML cache; improper format "+\
                "for separator tag line?"
            self.logger.error("{0}: {1}".format(msg, err))
            raise DjerbaHtmlCacheError(msg) from err
        elements = doc.getElementsByTagName('span')
        if len(elements)!=1:
            msg = "Failed to parse component name in HTML cache; expected "+\
                "exactly 1 <span> element, found "+(str(len(elements)))+\
                ": "+separator_line
            self.logger.error(msg)
            raise DjerbaHtmlCacheError(msg)
        elem = elements[0]
        if elem.hasAttribute(cc.COMPONENT_START):
            name = elem.getAttribute(cc.COMPONENT_START)
        elif elem.hasAttribute(cc.COMPONENT_END):
            name = elem.getAttribute(cc.COMPONENT_END)
        else:
            msg = "Failed to parse component name in HTML cache; no start/end "+\
                "attribute found in separator tag: "+separator_line
            self.logger.error(msg)
            raise DjerbaHtmlCacheError(msg)
        return name

    def update_cached_html(self, new_html, old_cache):
        # new_html = dictionary of HTML strings by component name
        # old_cache = encoded string of old HTML
        old_html = self.decode_from_base64(old_cache)
        old_lines = re.split("\n", old_html)
        new_lines = []
        replace_name = None
        for line in old_lines:
            if re.search(cc.COMPONENT_START, line):
                name = self.parse_name_from_separator(line)
                if name in new_html:
                    self.logger.debug("Updating "+name)
                    replace_name = name
                    new_lines.append(new_html[name])
                else:
                    self.logger.debug("No update found for "+name)
                    new_lines.append(line)
            elif replace_name:
                if re.search(cc.COMPONENT_END, line):
                    name = self.parse_name_from_separator(line)
                    if name != replace_name:
                        msg = "Mismatched separator names: start = "+replace_name+\
                            ", end = "+name
                        self.logger.error(msg)
                        raise DjerbaHtmlCacheError(msg)
                    else:
                        replace_name = None
            else:
                new_lines.append(line)
        if replace_name:
            msg = "No end tag found for component name '{0}'".format(replace_name)
            self.logger.error(msg)
            raise DjerbaHatmlCacheError(msg)
        self.logger.debug("HTML update done")
        return "\n".join(new_lines)

    def wrap_html(self, name, html):
        # place identifying tags before/after an HTML block, to facilitate later editing
        start = "<span {0}='{1}' />".format(cc.COMPONENT_START, name)
        end = "<span {0}='{1}' />".format(cc.COMPONENT_END, name)
        return "{0}\n{1}\n{2}\n".format(start, html, end)

class DjerbaHtmlCacheError(Exception):
    pass

