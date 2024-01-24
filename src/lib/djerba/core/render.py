"""
Class to render HTML from the JSON report data
Includes merge/deduplicate for shared tables, eg. gene info
"""

import json
import logging
import os
import pdfkit
from PyPDF2 import PdfMerger
import djerba.core.constants as cc
from djerba.util.environment import directory_finder, DjerbaEnvDirError
from djerba.util.image_to_base64 import converter
from djerba.util.logger import logger
from djerba.util.render_mako import mako_renderer

class html_renderer(logger):

    CLINICAL_HEADER_NAME = 'clinical_header.html'

    def __init__(self, core_data, log_level=logging.INFO, log_path=None):
        self.data = core_data
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.author = self.data[cc.AUTHOR]
        self.report_id = self.data[cc.REPORT_ID]
        finder = directory_finder(self.log_level, self.log_path)
        if finder.has_valid_core_html_dir():
            self.html_dir = finder.get_core_html_dir()
            self.logger.debug("Got HTML dir from environment: {0}".format(self.html_dir))
        else:
            self.html_dir = os.path.realpath(os.path.join(
                os.path.dirname(__file__),
                'html'
            ))
            msg = "No environment var for HTML dir, falling back to {0}".format(self.html_dir)
            self.logger.debug(msg)
        self.mako = mako_renderer(self.html_dir, self.log_level, self.log_path)
        config_path = os.path.join(self.html_dir, self.data[cc.DOCUMENT_CONFIG])
        self.logger.debug("Reading document config from {0}".format(config_path))
        with open(config_path) as config_file:
            self.config = json.loads(config_file.read())

    def _order_components(self, body, priorities):
        names = body.keys()
        ordered_names = sorted(names, key=lambda x: priorities[x])
        self.logger.debug('Priorities: {0}'.format(priorities))
        self.logger.debug('Ordered component names: {0}'.format(ordered_names))
        ordered_body = [body[x] for x in ordered_names]
        return ordered_body

    def get_document_header(self, doc_type):
        try:
            template_name = self.config[cc.DOCUMENT_SETTINGS][doc_type][cc.DOCUMENT_HEADER]
            stylesheet_name = self.config[cc.DOCUMENT_SETTINGS][doc_type][cc.STYLESHEET]
        except KeyError as err:
            msg = "Document config entry for '{0}' not found: {1}".format(doc_type, err)
            self.logger.error(msg)
            raise RuntimeError from err
        # do template substititon to insert the stylesheet
        with open(os.path.join(self.html_dir, stylesheet_name)) as in_file:
            stylesheet = in_file.read()
        args = {cc.STYLESHEET: stylesheet}
        header = self.mako.render_name(template_name, args)
        return header

    def get_document_footer(self, doc_type):
        try:
            file_name = self.config[cc.DOCUMENT_SETTINGS][doc_type][cc.DOCUMENT_FOOTER]
        except KeyError as err:
            template = "Footer entry for '{0}' not found in document config: {1}"
            msg = template.format(doc_type, err)
            self.logger.error(msg)
            raise
        # do template substitution for clinical footer; otherwise just read the file
        if doc_type == cc.CLINICAL:
            args = {cc.AUTHOR: self.author}
            footer = self.mako.render_name(file_name, args)
        else:
            with open(os.path.join(self.html_dir, file_name)) as footer_file:
                footer = footer_file.read()
        return footer

    def get_page_footer(self, doc_type):
        if doc_type == cc.CLINICAL:
            pdf_footer = "{0} - {1}".format('yyyy/mm/dd', self.report_id)
        elif doc_type == cc.RESEARCH:
            pdf_footer = 'For Research Use Only'
        else:
            pdf_footer = "{0} ".format('yyyy/mm/dd')
        return pdf_footer

    def run(self, html, priorities, attributes):
        """
        - Assemble HTML strings into one or more documents
        - Attributes determine which document a string belongs to
        - Priorities determine order within a document
        - Use the document config JSON file to get document headers/footers
        - The rest of the document is populated by plugin outputs in priority order

        Mockup of output data structure:
        data = {
            'documents': {
                'report_id_clinical': 'html text goes here',
                'report_id_research': 'different html text goes here'
            },
            'merge_list': ['report_id_clinical', 'report_id_research'],
            'merged_filename': 'report_id.pdf',
        }
        """
        data = {
            cc.DOCUMENTS: {},
            cc.PDF_FOOTERS: {}
        }
        merge_list = []
        for doc_type in self.config[cc.DOCUMENT_TYPES]:
            section_names = [x for x in html.keys() if doc_type in attributes[x]]
            section_html = {x:html[x] for x in section_names}
            if len(section_html) > 0:
                self.logger.info("Assembling HTML report document: {0}".format(doc_type))
                body_sections = self._order_components(section_html, priorities)
                document_sections = [self.get_document_header(doc_type), ]
                document_sections.extend(body_sections)
                document_sections.append(self.get_document_footer(doc_type))
                # doc_key is the prefix for HTML/PDF filenames
                doc_key = "{0}_report.{1}".format(self.report_id, doc_type)
                data[cc.DOCUMENTS][doc_key] = "\n".join(document_sections)
                data[cc.PDF_FOOTERS][doc_key] = self.get_page_footer(doc_type)
                merge_list.append(doc_key)
            else:
                self.logger.info("Omitting empty report document: {0}".format(doc_type))
        data[cc.MERGE_LIST] = merge_list
        data[cc.MERGED_FILENAME] = "{0}_report.pdf".format(self.report_id)
        
        return data

class pdf_renderer(logger):

    CLINICAL_SUFFIX = '.clinical.pdf'
    MERGED_SUFFIX = '.pdf'
    RESEARCH_SUFFIX = '.research.pdf'
    RESEARCH_FOOTER_TEXT = 'For Research Use Only'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        super().__init__()
        self.logger = self.get_logger(log_level, __name__, log_path)

    # Running the PDF renderer requires the wkhtmltopdf binary on the PATH
    # This can be done by loading the wkhtmltopdf environment module:
    # https://gitlab.oicr.on.ca/ResearchIT/modulator/-/blob/master/code/gsi/70_wkhtmltopdf.yaml

    # Current implementation runs with javascript disabled
    # If javascript is enabled, PDF rendering attempts a callout to https://mathjax.rstudio.com
    # With Internet access, this works; otherwise, it times out after ~4 minutes and PDF rendering completes
    # But rendering without Javascript runs successfully with no apparent difference in output
    # So it is disabled, to allow fast running on a machine without Internet (eg. cluster node)
    # See https://github.com/wkhtmltopdf/wkhtmltopdf/issues/4506
    # An alternative solution would be changing the HTML generation to omit unnecessary Javascript

    @staticmethod
    def merge_pdfs(pdf_path_list, out_path):
        merger = PdfMerger()
        for pdf in pdf_path_list:
            merger.append(pdf)
        merger.write(out_path)
        merger.close()

    def render_file(self, in_path, out_path, footer_text=None, footer=True):
        # create options, which are arguments to wkhtmltopdf for footer generation
        # the 'quiet' option suppresses chatter to STDOUT
        self.logger.info('Writing PDF to {0}'.format(out_path))
        if footer:
            if footer_text:
                self.logger.debug("Including page numbers and footer text")
                options = {
                    'footer-right': '[page] of [topage]',
                    'footer-left': footer_text,
                    'quiet': '',
                    'disable-javascript': ''
                }
            else:
                self.logger.debug("Including page numbers but no additional footer text")
                options = {
                    'footer-right': '[page] of [topage]',
                    'quiet': '',
                    'disable-javascript': ''
                }
        else:
            self.logger.info("Omitting PDF footer")
            options = {
                'quiet': '',
                'disable-javascript': ''
            }
        try:
            pdfkit.from_file(in_path, out_path, options=options)
        except Exception as err:
            msg = "Unexpected error of type "+\
                "{0} in PDF rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            trace = ''.join(traceback.format_tb(err.__traceback__))
            self.logger.error('Traceback: {0}'.format(trace))
            raise
        self.logger.info('Finished writing PDF')
