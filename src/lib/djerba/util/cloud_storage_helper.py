"""Cloud Storage helper using gcsfs for direct streaming via stdin"""

import os
import logging
import gcsfs
from djerba.util.logger import logger

class cloud_storage_helper(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.fs = None

    def _get_fs(self):
        if self.fs is None:
            # Create GCS filesystem client. Uses default credentials in the cloud.
            self.fs = gcsfs.GCSFileSystem()
        return self.fs

    def is_gcs_path(self, path):
        return isinstance(path, str) and path.startswith('gs://')

    def open(self, path, mode='rb'):
        """Open a file directly from GCS (returns a gcsfs object) or local filesystem"""
        if self.is_gcs_path(path):
            self.logger.info(f"Opening GCS stream: {path}")
            return self._get_fs().open(path, mode=mode)
        else:
            self.logger.info(f"Opening local file: {path}")
            # Ensure local path is absolute if it's not already
            abs_path = os.path.abspath(os.path.expanduser(path))
            return open(abs_path, mode=mode)

    def run_with_stdin(self, command, gcs_path, **kwargs):
        # Launch external program
        # Runs a subprocess with a GCS file piped to stdin
        import subprocess
        
        if self.is_gcs_path(gcs_path):
            with self.open(gcs_path) as f:
                self.logger.info(f"Piping {gcs_path} to command stdin")
                return subprocess.run(command, stdin=f, capture_output=True, **kwargs)
        else:
            with open(gcs_path, 'rb') as f:
                return subprocess.run(command, stdin=f, capture_output=True, **kwargs)
            return None
