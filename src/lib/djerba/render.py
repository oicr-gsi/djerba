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
        self.logger.info("Djerba HTML rendering finished; wrote output to {0}".format(out_path))
        return result

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

    def run(self, html_path, pdf_path, analysis_unit):
        """Render HTML to PDF"""
        # create options, which are arguments to wkhtmltopdf for footer generation
        # the 'quiet' option suppresses chatter to STDOUT
        options = {
            'footer-right': '[page] of [topage]',
            'footer-center': analysis_unit,
            'quiet': '',
            'disable-javascript': ''
        }
        self.logger.info('Writing PDF for analysis unit "{0}" to {1}'.format(analysis_unit, pdf_path))
        pdfkit.from_url(html_path, pdf_path, options = options)
        self.logger.info('Finished writing PDF')
