
import logging
import traceback
from mako.lookup import TemplateLookup
from djerba.util.logger import logger

class mako_renderer(logger):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def get_template(self, template_dir, filename):
        # strict_undefined=True provides an informative error for missing variables in JSON
        # see https://docs.makotemplates.org/en/latest/runtime.html#context-variables
        report_lookup = TemplateLookup(directories=[template_dir, ], strict_undefined=True)
        return report_lookup.get_template(filename)

    def render_template(self, mako_template, args):
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type "+\
                "{0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            trace = ''.join(traceback.format_tb(err.__traceback__))
            self.logger.error('Traceback: {0}'.format(trace))
            raise
        return html
