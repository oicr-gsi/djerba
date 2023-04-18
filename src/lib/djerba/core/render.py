"""
Class to render HTML from the JSON report data
Includes merge/deduplicate for shared tables, eg. gene info
"""

import logging
import os
import traceback
import djerba.util.ini_fields as ini
from djerba.util.logger import logger
from mako.lookup import TemplateLookup


class renderer(logger):

    CLINICAL_HEADER_NAME = 'clinical_header.html'

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            'html'
        ))
        # strict_undefined=True provides an informative error for missing variables in JSON
        # see https://docs.makotemplates.org/en/latest/runtime.html#context-variables
        report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
        self.logger.debug("Loading clinical header Mako template")
        self.clinical_header_template = report_lookup.get_template(self.CLINICAL_HEADER_NAME)

    def render_header(self, data):
        return self.render_from_template(self.clinical_header_template, data.get(ini.CORE))

    def render_from_template(self, mako_template, args):
        """General-purpose method to run a mako template and log any errors"""
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            trace = ''.join(traceback.format_tb(err.__traceback__))
            self.logger.error('Traceback: {0}'.format(trace))
            raise
        return html

    def run(self, data):
        header = self.render_header(data)
        footer_template = """
        <div>{0}</div>
        </body>
        </html>
        """
        footer = footer_template.format(data['comment'])
        return [header, footer]
