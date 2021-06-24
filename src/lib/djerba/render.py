"""
Publish Djerba results in human-readable format.
Wrap an Rmarkdown script to output HTML from a Djerba results directory.
"""

import os
import subprocess
import djerba.ini_fields as ini

class html_renderer:

    R_MARKDOWN_DIRNAME = 'R_markdown'

    def __init__(self, config):
        self.r_script_dir = config[ini.SETTINGS].get(ini.R_SCRIPT_DIR)
        if not self.r_script_dir:
            self.r_script_dir = os.path.join(os.path.dirname(__file__), self.R_MARKDOWN_DIRNAME)
        self.markdown_script = os.path.join(self.r_script_dir, 'html_report.Rmd')

    def write_html(self, report_dir, out_path):
        """Read the reporting directory, and use the Rmarkdown script to write HTML"""
        render = "\"rmarkdown::render('{0}', output_file = '{1}')\"".format(self.markdown_script, out_path)
        cmd = [
            'Rscript', '-e',
            render,
            report_dir
        ]
        print('###', ' '.join(cmd))
        result = subprocess.run(cmd, check=True, capture_output=True)
        return result



