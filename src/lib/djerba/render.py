"""
Publish Djerba results in human-readable format.
Wrap an Rmarkdown script to output HTML from a Djerba results directory.
Subsequently use pdfkit to convert the HTML to PDF.
"""

import logging
import os
import pdfkit
import subprocess
import djerba.util.constants as constants
from djerba.util.logger import logger

class html_renderer(logger):

    R_MARKDOWN_DIRNAME = 'R_markdown'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        r_script_dir = os.path.join(os.path.dirname(__file__), self.R_MARKDOWN_DIRNAME)
        self.markdown_script = os.path.join(r_script_dir, 'html_report.Rmd')

    def run(self, report_dir, out_path):
        """Read the reporting directory, and use the Rmarkdown script to write HTML"""
        # no need for double quotes around the '-e' argument; subprocess does not use a shell
        render = "rmarkdown::render('{0}', output_file = '{1}')".format(self.markdown_script, out_path)
        cmd = [
            'Rscript', '-e',
            render,
            report_dir
        ]
        self.logger.info('Rendering HTML with Rmarkdown command "'+' '.join(cmd)+'"')
        result = subprocess.run(cmd, capture_output=True)
        try:
            result.check_returncode()
        except subprocess.CalledProcessError:
            self.logger.error("Unexpected error from Rmarkdown script")
            self.logger.error("Rmarkdown STDOUT: "+result.stdout.decode(constants.TEXT_ENCODING))
            self.logger.error("Rmarkdown STDERR: "+result.stderr.decode(constants.TEXT_ENCODING))
            raise
        return result

class pdf_renderer(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)

    def run(self, html_path, pdf_path):
        """Render HTML to PDF"""
        #create options, which are arguments to wkhtmltopdf for footer generation
        options = {
            'footer-right': '[page] of [topage]',
            'footer-left': '[date]',
            'footer-center': '${ANALYSIS_UNIT}' # TODO ensure env variable is present
        }
        self.logger.warning('Omitting PDF output; renderer still in development')
        #pdfkit.from_url(html_path, pdf_path, options = options)
