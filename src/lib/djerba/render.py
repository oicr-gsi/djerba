"""
Publish Djerba results in human-readable format.
Wrap an Rmarkdown script to output HTML from a Djerba results directory.
Subsequently use pdfkit to convert the HTML to PDF.
"""

import logging
import os
import pdfkit
import subprocess
import tempfile
import time
from string import Template
import djerba.util.constants as constants
from djerba.util.logger import logger

class html_renderer(logger):

    R_MARKDOWN_DIRNAME = 'R_markdown'
    AFTER_BODY = 'DJERBA_RMD_AFTER_BODY'
    FOOTER_TEMPLATE_40X = 'footer-40x.html'
    FOOTER_TEMPLATE_80X = 'footer-80x.html'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        r_script_dir = os.path.join(os.path.dirname(__file__), self.R_MARKDOWN_DIRNAME)
        self.default_script = os.path.join(r_script_dir, 'html_report_default.Rmd')
        self.fail_script = os.path.join(r_script_dir, 'html_report_failed.Rmd')
        self.data_dir = os.path.join(os.path.dirname(__file__), constants.DATA_DIR_NAME)

    def run(self, report_dir, out_path, target_coverage, failed=False, cgi_author=None):
        """Read the reporting directory, and use an Rmarkdown script to write HTML"""
        # no need for double quotes around the '-e' argument; subprocess does not use a shell
        if failed:
            markdown_script = self.fail_script
        else:
            markdown_script = self.default_script
        cgi_author = cgi_author if cgi_author!=None else 'CGI_PLACEHOLDER'
        with tempfile.TemporaryDirectory(prefix='djerba_html_footer_') as tmp:
            # write footer file, customized with author and date
            if target_coverage==40:
                template_path = os.path.join(self.data_dir, self.FOOTER_TEMPLATE_40X)
            elif target_coverage==80:
                template_path = os.path.join(self.data_dir, self.FOOTER_TEMPLATE_80X)
            else:
                msg = "Target coverage '{0}' is not supported for HTML output".format(target_coverage)
                self.logger.error(msg)
                raise ValueError(msg)
            settings = {
                "CGI_AUTHOR": cgi_author,
                "DATE": time.strftime("%Y/%m/%d")
            }
            self.logger.debug("Writing HTML footer with template {0}, settings {1}".format(template_path, settings))
            footer_path = os.path.join(tmp, 'djerba_footer.html')
            # TODO generate all HTML from a single template, eg. in Jinja
            with open(template_path) as in_file, open(footer_path, 'w') as out_file:
                src = Template(in_file.read())
                out_file.write(src.substitute(settings))
            os.environ[self.AFTER_BODY] = footer_path
            self.logger.debug(
                "Target coverage {0}, using footer file {1}".format(target_coverage, os.environ[self.AFTER_BODY])
            )
            render = "rmarkdown::render('{0}', output_file = '{1}')".format(markdown_script, out_path)
            cmd = [
                'Rscript', '-e',
                render,
                os.path.abspath(report_dir)
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

    def run(self, html_path, pdf_path, analysis_unit=None, footer=True):
        """Render HTML to PDF"""
        # create options, which are arguments to wkhtmltopdf for footer generation
        # the 'quiet' option suppresses chatter to STDOUT
        self.logger.info('Writing PDF to {0}'.format(pdf_path))
        if footer:
            self.logger.info("Including footer text for CGI clinical report")
            if not analysis_unit:
                self.logger.warning("No analysis unit specified; using placeholder for PDF footer")
                analysis_unit = "ANALYSIS_UNIT_PLACEHOLDER"
            options = {
                'footer-right': '[page] of [topage]',
                'footer-center': analysis_unit,
                'quiet': '',
                'disable-javascript': ''
            }
        else:
            self.logger.info("Omitting footer text")
            options = {
                'quiet': '',
                'disable-javascript': ''
            }
        pdfkit.from_file(html_path, pdf_path, options = options)
        self.logger.info('Finished writing PDF')
