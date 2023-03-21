"""Base class with method to run a subprocess"""

import logging
import subprocess
from collections import Iterable
from djerba.util.logger import logger
import djerba.util.constants as constants

class subprocess_runner(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)

    def run(self, command, description='subprocess', redact=[], stdin=None, raise_err=True):
        msg = None
        if isinstance(command, str) or not isinstance(command, Iterable):
            msg = "Command must be a non-string iterable: Received {0}".format(command)
            self.logger.error(msg)
            raise ValueError(msg)
        if len(redact) > 0:
            # redact selected arguments from logging, eg. passwords, access tokens
            command_redacted = command.copy()
            for i in range(len(command_redacted)):
                if command_redacted[i] in redact:
                    command_redacted[i+1] = '***REDACTED***'
            logged_command = ' '.join(command_redacted)
        else:
            logged_command = ' '.join(command)
        self.logger.info("Running {0}: '{1}'".format(description, logged_command))        
        result = subprocess.run(
            command,
            input = stdin,
            capture_output=True,
            encoding=constants.TEXT_ENCODING,
        )
        stdout = result.stdout
        stderr = result.stderr
        try:
            result.check_returncode()
        except subprocess.CalledProcessError as err:
            self.logger.error("Failed to run {0}: {1}".format(description, err))
            self.logger.error("{0} STDOUT: '{1}'".format(description, stdout))
            self.logger.error("{0} STDERR: '{1}'".format(description, stderr))
            if raise_err:
                raise
        self.logger.info("Successfully ran {0}".format(description))
        self.logger.debug("{0} STDOUT: '{1}'".format(description, stdout))
        self.logger.debug("{0} STDERR: '{1}'".format(description, stderr))
        return result
