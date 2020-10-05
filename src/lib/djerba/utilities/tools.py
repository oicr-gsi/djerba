"""General-purpose utility functions"""

import gzip
import os
import re
import shutil
import subprocess
import time

class system_tools:

    """Class for system utility functions"""

    @staticmethod
    def run_subprocesses(commands, logger, shell=True, max_processes=4, max_time=14400):
        """Run commands in parallel; limits on maximum running at once, and timeout"""
        total = len(commands)
        processes = set()
        logger.debug("Running %i subprocess commands" % total)
        for cmd in commands:
            logger.info("Running subprocess command: %s" % cmd)
            processes.add(subprocess.Popen(cmd, shell=shell, stderr=subprocess.PIPE, stdout=subprocess.PIPE))
            if len(processes) >= max_processes:
                os.wait()
                processes.difference_update([p for p in processes if p.poll() is not None])
        # all commands have been launched; wait for completion
        start = time.time()
        while(any([p.poll()==None for p in processes])):
            time.sleep(5)
            if time.time() - start > max_time:
                msg = "Exceeded timeout of %i seconds" % max_time
                logger.error(msg)
                raise RuntimeError(msg)
        logger.info("Finished running %i subprocesses (run with debug logging to view stdout/stderr)" % total)
        for p in processes:
            logger.debug("STDOUT status %i, command '%s': '%s'" % (p.returncode, str(p.args), p.stdout.read()))
            logger.debug("STDERR status %i, command '%s': '%s'" % (p.returncode, str(p.args), p.stderr.read()))
            p.stdout.close()
            p.stderr.close()
        # check return codes
        failed = [p for p in processes if p.returncode!=0]
        if len(failed)>0:
            for f in failed:
                msg = "Non-zero exit status %i from command %s" % (f.returncode, str(f.args))
                logger.error(msg)
            msg = "%i of %i commands had non-zero exit status; see log output for details" % (len(failed), len(commands))
            logger.error(msg)
            raise RuntimeError(msg)
        else:
            logger.info("%i of %i subprocess return codes are zero" % (total, total))

    @staticmethod
    def decompress_gzip(input_paths, out_dir):
        """Gunzip a list of file paths ending in .gz; return decompressed filenames"""
        decompressed = []
        for src_path in input_paths:
            if not re.search("\.gz$", src_path):
                raise OSError("Path to be decompressed does not end in .gz: %s" % src_path)
            dest_name = re.split('\.gz$', os.path.basename(src_path)).pop(0)
            decompressed.append(dest_name)
            dest_path = os.path.join(out_dir, dest_name)
            with gzip.open(src_path) as src_file, open(dest_path, 'wb') as dest_file:
                shutil.copyfileobj(src_file, dest_file)
        return decompressed
