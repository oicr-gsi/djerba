"""Classes to handle command-line arguments"""

import logging
from djerba.util.logger import logger
from djerba.util.validator import path_validator

class arg_processor_base(logger):
    # class to process command-line args for creating a main object

    def __init__(self, args, logger=None, validate=True):
        self.args = args
        # set self.log_level, self.log_path in case we need to make a new logger object
        # TODO see if log path can be extracted from existing logger (if any)
        # for now, use value in args as a fallback
        self.log_path = self._get_validated_log_path(args)
        if logger:
            # do not call 'get_logger' if one has already been configured
            # this way, we can preserve the level/path of an existing logger
            self.logger = logger
            self.log_level = logger.level
        else:
            self.log_level = self.get_args_log_level(self.args)
            self.logger = self.get_logger(self.log_level, __name__, self.log_path)
        if validate:
            self.validate_args(self.args)  # checks subparser and args are valid
        self.mode = self.args.subparser_name

    def _get_arg(self, arg_name):
        try:
            value = getattr(self.args, arg_name)
        except AttributeError as err:
            msg = "Argument {0} not defined in script mode {1}".format(arg_name, self.mode)
            self.logger.error(msg)
            raise ArgumentNameError(msg) from err
        return value

    def _get_validated_log_path(self, args):
        # return a validated log output path, or None
        # we are verifying the log path, so don't write output there yet
        if args.log_path != None:
            path_validator(self.log_level).validate_output_file(args.log_path)
        return args.log_path

    def get_json(self):
        return self._get_arg('json')

    def get_log_level(self):
        return self.log_level

    def get_log_path(self):
        return self.log_path

    def get_mode(self):
        return self.mode

    def get_out_dir(self):
        return self._get_arg('out_dir')

    def is_forced(self):
        return self._get_arg('force')

    def is_pdf_enabled(self):
        return self._get_arg('pdf')

    def is_write_json_enabled(self):
        return self._get_arg('write_json')

    def validate_args(self, args):
        self.logger.warning("Placeholder validate_args method, should override in subclass")


class ArgumentNameError(Exception):
    pass
