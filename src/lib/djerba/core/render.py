"""
Class to render HTML from the JSON report data
Includes merge/deduplicate for shared tables, eg. gene info
"""

import logging
import os
import djerba.core.constants as cc
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.render_mako import mako_renderer

class renderer(logger):

    CLINICAL_HEADER_NAME = 'clinical_header.html'

    def __init__(self, core_data, log_level=logging.INFO, log_path=None):
        self.data = core_data
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        if os.environ.get(cc.DJERBA_CORE_HTML_DIR_VAR):
            self.html_dir = os.environ.get(cc.DJERBA_CORE_HTML_DIR_VAR)
        else:
            self.html_dir = os.path.realpath(os.path.join(
                os.path.dirname(__file__),
                'html'
            ))

    def _is_clinical(self, attributes):
        is_clinical = cc.CLINICAL in attributes \
            and cc.SUPPLEMENTARY not in attributes
        return is_clinical

    def _is_supplementary(self, attributes):
        is_supplementary = cc.CLINICAL not in attributes \
            and cc.SUPPLEMENTARY in attributes
        return is_supplementary

    def _order_components(self, body, priorities):
        names = body.keys()
        ordered_names = sorted(names, key=lambda x: priorities[x])
        self.logger.debug('Priorities: {0}'.format(priorities))
        self.logger.debug('Ordered component names: {0}'.format(ordered_names))
        ordered_body = [body[x] for x in ordered_names]
        return ordered_body

    def _read_from_html_dir(self, filename):
        try:
            with open(os.path.join(self.html_dir, filename)) as in_file:
                contents = in_file.read()
        except FileNotFoundError as err:
            self.logger.error("Cannot read core HTML file: {0}".format(err))
            raise
        return contents

    def get_header_and_stylesheet(self):
        mako = mako_renderer(self.log_level, self.log_path)
        template = mako.get_template(self.html_dir, self.data.get(cc.CLINICAL_HEADER))
        stylesheet = self._read_from_html_dir(self.data.get(cc.STYLESHEET))
        return mako.render_template(template, {'stylesheet': stylesheet})

    def get_logo(self):
        oicr_logo_path = os.path.join(self.html_dir, self.data.get(cc.LOGO))
        cv = converter(self.log_level, self.log_path)
        png = cv.convert_png(oicr_logo_path, 'OICR logo')
        img = '<img width="105" height="72" style="padding: 0px 0px 0px 0px; " src="{0}"'
        return img.format(png)

    def get_preamble(self):
        return self._read_from_html_dir(self.data.get(cc.PREAMBLE))

    def get_footer(self):
        mako = mako_renderer(self.log_level, self.log_path)
        template = mako.get_template(self.html_dir, self.data.get(cc.CLINICAL_FOOTER))
        return mako.render_template(template, {'author': self.data.get(cc.AUTHOR)})

    def run(self, body, priorities, attributes):
        all_html = []
        all_html.append(self.get_header_and_stylesheet())
        all_html.append(self.get_logo())
        all_html.append(self.get_preamble())
        # make the clinical report section
        report_names = [x for x in body.keys() if self._is_clinical(attributes[x])]
        report_body = {x:body[x] for x in report_names}
        all_html.extend(self._order_components(report_body, priorities))
        # TODO generate research-use-only as a separate HTML document
        # append the document footer and return as a string
        all_html.append(self.get_footer())
        html_string = "\n".join(all_html)
        return html_string
