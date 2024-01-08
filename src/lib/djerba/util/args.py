"""Classes to handle command-line arguments"""

import logging
from djerba.util.logger import logger

class arg_processor_base(logger):
    # class to process command-line args for creating a main object

    DEFAULT_JSON_FILENAME = 'djerba_report.json'

    def __init__(self, args, logger=None, validate=True):
        self.args = args
        if logger:
            # do not call 'get_logger' if one has already been configured
            # this way, we can preserve the level/path of an existing logger
            self.logger = logger
        else:
            self.log_level = self.get_args_log_level(self.args)
            self.log_path = self.args.log_path
            if self.log_path:
                # we are verifying the log path, so don't write output there yet
                path_validator(self.log_level).validate_output_file(self.log_path)
            self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        if validate:
            self.validate_args(self.args)  # checks subparser and args are valid
        self.mode = self.args.subparser_name

    def _get_arg(self, arg_name):
        try:
            value = getattr(self.args, arg_name)
        except AttributeError as err:
            msg = "Argument {0} not defined in Djerba mode {1}".format(arg_name, self.mode)
            self.logger.error(msg)
            raise ArgumentNameError(msg) from err
        return value

    def is_pdf_enabled(self):
        return self._get_arg('pdf')

    def is_write_json_enabled(self):
        return self._get_arg('write_json')

    def get_log_level(self):
        return self.log_level

    def get_log_path(self):
        return self.log_path

    def get_mode(self):
        return self.mode

    def get_out_dir(self):
        return self._get_arg('out_dir')


class ArgumentNameError(Exception):
    pass
