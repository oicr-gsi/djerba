"""
Publish Djerba results in human-readable format.
Wrap an Rmarkdown script to output HTML from a Djerba results directory.
Subsequently use pdfkit to convert the HTML to PDF.
"""

import csv
import logging
import os
import pdfkit
import subprocess
import tempfile
import time
from shutil import copy
from string import Template
import djerba.util.constants as constants
from djerba.util.logger import logger

class html_renderer(logger):

    R_MARKDOWN_DIRNAME = 'R_markdown'
    AFTER_BODY = 'DJERBA_RMD_AFTER_BODY'
    FOOTER_TEMPLATE_40X = 'footer-40x.html'
    FOOTER_TEMPLATE_80X = 'footer-80x.html'
    DEFAULT_RMD = 'html_report_default.Rmd'
    FAILED_RMD = 'html_report_failed.Rmd'

    
    # constants to construct fusion remapping
    DATA_FUSION_NEW = 'data_fusions_new_delimiter.txt'
    DATA_FUSION_OLD = 'data_fusions.txt'
    FUSION_INDEX = 4

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.r_script_dir = os.path.join(os.path.dirname(__file__), self.R_MARKDOWN_DIRNAME)

    def _read_fusion_remapping(self, report_dir):
        """Construct a dictionary from the 'Fusion' column in old and new formats"""
        with open(os.path.join(report_dir, self.DATA_FUSION_OLD)) as file_old:
            old = [row[self.FUSION_INDEX] for row in csv.reader(file_old, delimiter="\t")]
        with open(os.path.join(report_dir, self.DATA_FUSION_NEW)) as file_new:
            new = [row[self.FUSION_INDEX] for row in csv.reader(file_new, delimiter="\t")]
        if len(old) != len(new):
            msg = "Fusion ID lists from {0} are of unequal length".format(report_dir)
            self.logger.error(msg)
            raise RuntimeError(msg)
        # first item of each list is the header, which can be ignored
        return {old[i]:new[i] for i in range(1, len(old))}

    def run(self, report_dir, out_path, target_coverage, failed=False, cgi_author=None):
        """Read the reporting directory, and use an Rmarkdown script to write HTML"""
        # TODO replace the Rmarkdown; separate out the computation and HTML templating
        cgi_author = cgi_author if cgi_author!=None else 'CGI_PLACEHOLDER'
        if target_coverage==40:
            template_path = os.path.join(self.r_script_dir, self.FOOTER_TEMPLATE_40X)
        elif target_coverage==80:
            template_path = os.path.join(self.r_script_dir, self.FOOTER_TEMPLATE_80X)
        else:
            msg = "Target coverage '{0}' is not supported for HTML output".format(target_coverage)
            self.logger.error(msg)
            raise ValueError(msg)
        os.environ[self.AFTER_BODY] = template_path
        self.logger.debug(
            "Target coverage {0}, using footer template {1}".format(target_coverage, os.environ[self.AFTER_BODY])
        )
        # copy files as a workaround; horribly, Rmarkdown insists on changing its working directory
        with tempfile.TemporaryDirectory(prefix='djerba_html_') as tmp:
            tmp_out_path = os.path.join(tmp, 'djerba.html')
            for filename in os.listdir(self.r_script_dir):
                copy(os.path.join(self.r_script_dir, filename), tmp)
            if failed:
                markdown_script = os.path.join(tmp, self.FAILED_RMD)
            else:
                markdown_script = os.path.join(tmp, self.DEFAULT_RMD)
            # no need for double quotes around the '-e' argument; subprocess does not use a shell
            render = "rmarkdown::render('{0}', output_file = '{1}')".format(markdown_script, tmp_out_path)
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
            self.logger.debug("Wrote HTML to {0}".format(tmp_out_path))
            self.postprocess(tmp_out_path, out_path, report_dir, cgi_author)
        self.logger.info("Djerba HTML rendering finished; wrote output to {0}".format(out_path))
        return result

    def postprocess(self, in_path, out_path, report_dir, cgi_author):
        """Postprocessing for the HTML report"""
        # Hacked solution to modify the Rmarkdown output; TODO replace with an improved HTML template
        self.logger.debug("Postprocessing the HTML report")
        fusions = self._read_fusion_remapping(report_dir)
        with open(in_path) as in_file, open(out_path, 'w') as out_file:
            report = in_file.read()
            report = report.replace('DJERBA_REPORT_AUTHOR', cgi_author)
            report = report.replace('DJERBA_REPORT_DATE', time.strftime("%Y/%m/%d"))
            for fusion_id in fusions.keys():
                report = report.replace(fusion_id, fusions[fusion_id])
            out_file.write(report)
        self.logger.debug("Finished postprocessing {0} to {1}".format(in_path, out_path))

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

    def run(self, html_path, pdf_path, footer_text=None, footer=True):
        """Render HTML to PDF"""
        # create options, which are arguments to wkhtmltopdf for footer generation
        # the 'quiet' option suppresses chatter to STDOUT
        self.logger.info('Writing PDF to {0}'.format(pdf_path))
        if footer:
            if footer_text:
                self.logger.info("Including footer text for CGI clinical report")
                options = {
                    'footer-right': '[page] of [topage]',
                    'footer-center': footer_text,
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
        pdfkit.from_file(html_path, pdf_path, options = options)
        self.logger.info('Finished writing PDF')
