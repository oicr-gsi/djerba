"""
Render Djerba results in HTML and PDF format
"""

import json
import logging
import os
import pdfkit
from PyPDF2 import PdfMerger
import traceback

from mako.template import Template
from mako.lookup import TemplateLookup

import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.render.archiver import archiver
from djerba.util.logger import logger

class html_renderer(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
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
        report_lookup = TemplateLookup(directories=[html_dir,], strict_undefined=True)
        self.clinical_template = report_lookup.get_template("clinical_report_template.html")
        self.research_template = report_lookup.get_template("research_report_template.html")

    def run(self, in_path, out_path, clinical_or_research="clinical", archive=True):
        if(clinical_or_research == "clinical"):
            self.template = self.clinical_template
            out_path = out_path + ".clinical.html"
        elif (clinical_or_research == "research"):
            self.template = self.research_template
            out_path = out_path + ".research.html"
        else:
            print('err')
        with open(in_path) as in_file:
            data = json.loads(in_file.read())
            args = data.get(constants.REPORT)
            config = data.get(constants.SUPPLEMENTARY).get(constants.CONFIG)

        with open(out_path, 'w') as out_file:
            try:
                html = self.template.render(**args)
            except Exception as err:
                msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
                self.logger.error(msg)
                trace = ''.join(traceback.format_tb(err.__traceback__))
                self.logger.error('Traceback: {0}'.format(trace))
                raise
            print(html, file=out_file)
        if archive:
            uploaded, report_id = archiver(self.log_level, self.log_path).run(in_path)
            if uploaded == True: self.logger.info(f"Archiving successful: {report_id}")
            else: self.logger.warning(f"Error! Archiving unsuccessful: {report_id}")
        else:
            self.logger.info("Archive operation not requested; omitting archiving")
        self.logger.info("Completed HTML rendering of {0} to {1}".format(in_path, out_path))

class pdf_renderer(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
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

    def run(self, html_path, pdf_path, clinical_or_research="clinical", footer_text=None, footer=True):
        """Render HTML to PDF"""
        # create options, which are arguments to wkhtmltopdf for footer generation
        # the 'quiet' option suppresses chatter to STDOUT
        if(clinical_or_research == "clinical"):
            html_path = html_path + ".clinical.html"
            pdf_path = pdf_path + ".clinical.pdf"
        elif (clinical_or_research == "research"):
            html_path = html_path + ".research.html"
            pdf_path = pdf_path + ".research.pdf"
        else:
            print('err')
        self.logger.info('Writing PDF to {0}'.format(pdf_path))
        if footer:
            if footer_text and clinical_or_research == "clinical" :
                self.logger.info("Including footer text for CGI clinical report")
                options = {
                    'footer-right': '[page] of [topage]',
                    'footer-left': footer_text,
                    'quiet': '',
                    'disable-javascript': ''
                }
            elif footer_text and clinical_or_research == "research":
                self.logger.info("Including footer text for CGI clinical report")
                options = {
                    'footer-right': '[page] of [topage]',
                    'footer-left': "For Research-Use Only",
                    'quiet': '',
                    'disable-javascript': ''
                }
            else:
                self.logger.info("Including page numbers but no additional footer text")
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
            pdfkit.from_file(html_path, pdf_path, options = options)
        except Exception as err:
            msg = "Unexpected error of type {0} in PDF rendering: {0}".format(type(err).__name__, err)
            self.logger.error(msg)
            trace = ''.join(traceback.format_tb(err.__traceback__))
            self.logger.error('Traceback: {0}'.format(trace))
            raise
        self.logger.info('Finished writing PDF')

    def merge_clinical_research(self, pdf_path):
        clinical_pdf_path = pdf_path+".clinical.pdf"
        research_pdf_path = pdf_path+".research.pdf"
        merged_pdf_path = pdf_path+".report.pdf"
        self.merge_pdfs(clinical_pdf_path,research_pdf_path,merged_pdf_path)

    def merge_pdfs(self,pdf1,pdf2,output):
        pdfs = [pdf1,pdf2]
        merger = PdfMerger()
        for pdf in pdfs:
            merger.append(pdf)
        merger.write(output+".report.pdf")
        merger.close()

