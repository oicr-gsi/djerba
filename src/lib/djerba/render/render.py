"""
Render Djerba results in HTML and PDF format
"""

import json
import logging
import os
import traceback
from datetime import datetime

import djerba.util.constants as constants
import pdfkit
from PyPDF2 import PdfMerger
from djerba.render.archiver import archiver
from djerba.util.logger import logger
from mako.lookup import TemplateLookup


class html_renderer(logger):
    # mode names for report format
    CLINICAL_TEMPLATE_NAME = 'clinical_report_template.html'
    RESEARCH_TEMPLATE_NAME = 'research_report_template.html'
    CLINICAL_SUFFIX = '.clinical.html'
    RESEARCH_SUFFIX = '.research.html'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        super().__init__()
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'html'
        ))
        # strict_undefined=True provides an informative error for missing variables in JSON
        # see https://docs.makotemplates.org/en/latest/runtime.html#context-variables
        report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
        self.logger.debug("Loading clinical Mako template")
        self.clinical_template = report_lookup.get_template(self.CLINICAL_TEMPLATE_NAME)
        self.logger.debug("Loading research Mako template")
        self.research_template = report_lookup.get_template(self.RESEARCH_TEMPLATE_NAME)

    def render(self, in_path, out_dir, out_file_prefix, out_file_suffix, mako_template, archive=True):
        out_path = os.path.realpath(os.path.join(out_dir, out_file_prefix + out_file_suffix))
        with open(in_path) as in_file:
            data = json.loads(in_file.read())
            args = data.get(constants.REPORT)
        with open(out_path, 'w', encoding=constants.TEXT_ENCODING) as out_file:
            try:
                html = mako_template.render(**args)
            except Exception as err:
                msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
                self.logger.error(msg)
                trace = ''.join(traceback.format_tb(err.__traceback__))
                self.logger.error('Traceback: {0}'.format(trace))
                raise
            print(html, file=out_file)
        if archive:
            uploaded, report_id = archiver(self.log_level, self.log_path).run(in_path)
            if uploaded:
                self.logger.info(f"Archiving successful: {report_id}")
            else:
                self.logger.warning(f"Error! Archiving unsuccessful: {report_id}")
        else:
            self.logger.info("Archive operation not requested; omitting archiving")
        self.logger.info("Completed HTML rendering of {0} to {1}".format(in_path, out_path))
        return out_path

    def run_clinical(self, in_path, out_dir, out_file_prefix, archive):
        self.logger.info("Rendering HTML for clinical report")
        return self.render(in_path, out_dir, out_file_prefix, self.CLINICAL_SUFFIX, self.clinical_template, archive)

    def run_research(self, in_path, out_dir, out_file_prefix, archive):
        self.logger.info("Rendering HTML for research report")
        return self.render(in_path, out_dir, out_file_prefix, self.RESEARCH_SUFFIX, self.research_template, archive)


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
    def merge_pdfs(pdf1, pdf2, output):
        pdfs = [pdf1, pdf2]
        merger = PdfMerger()
        for pdf in pdfs:
            merger.append(pdf)
        merger.write(output)
        merger.close()

    def render(self, in_path, out_dir, out_file_prefix, out_file_suffix,
               footer_text=None, footer=True):
        """
        Render HTML to PDF
        out_file_prefix is typically the report ID
        """
        out_path = os.path.realpath(os.path.join(out_dir, out_file_prefix + out_file_suffix))
        self.render_path(in_path, out_path, footer_text, footer)
        return out_path

    def render_path(self, in_path, out_path, footer_text=None, footer=True):
        # create options, which are arguments to wkhtmltopdf for footer generation
        # the 'quiet' option suppresses chatter to STDOUT
        self.logger.info('Writing PDF to {0}'.format(out_path))
        if footer:
            if footer_text:
                self.logger.debug("Including page numbers and footer text")
                current_date = datetime.now()
                options = {
                    'footer-right': '[page] of [topage]',
                    'footer-left': ' - '.join((current_date.strftime('%Y-%m-%d'), footer_text)),
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
            msg = "Unexpected error of type {0} in PDF rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            trace = ''.join(traceback.format_tb(err.__traceback__))
            self.logger.error('Traceback: {0}'.format(trace))
            raise
        self.logger.info('Finished writing PDF')

    def run_all(self, clinical_html, research_html, out_dir, out_file_prefix, footer_text):
        out_dir = os.path.realpath(out_dir)
        clinical_pdf = self.run_clinical(clinical_html, out_dir, out_file_prefix, footer_text)
        research_pdf = self.run_research(research_html, out_dir, out_file_prefix)
        self.logger.info("Merging clinical and research report PDFs")
        merged_pdf = os.path.join(out_dir, out_file_prefix + self.MERGED_SUFFIX)
        self.merge_pdfs(clinical_pdf, research_pdf, merged_pdf)
        return merged_pdf

    def run_clinical(self, in_path, out_dir, out_file_prefix, footer_text):
        self.logger.info("Rendering PDF for clinical report")
        return self.render(in_path,
                           out_dir,
                           out_file_prefix,
                           self.CLINICAL_SUFFIX,
                           footer_text)

    def run_research(self, in_path, out_dir, out_file_prefix):
        self.logger.info("Rendering PDF for research report")
        return self.render(in_path,
                           out_dir,
                           out_file_prefix,
                           self.RESEARCH_SUFFIX,
                           self.RESEARCH_FOOTER_TEXT)
