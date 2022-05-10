"""Code to archive files to a given directory for later reference"""

import json
import constants

class archiver(logger):
    """Archive the report JSON to a directory, with hashing to avoid overwrites"""

    # TODO read "patient_info"-> "Tumour Sample ID" to get directory name
    
    def __init__(self, ini_path, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)
        with open(ini_path) as ini_file:
            self.config_string = ini_file.read()



        self.config = configparser.ConfigParser()
        self.config.read_string(self.config_string)
        self.patient_id = self.config.get(ini.DISCOVERED, ini.PATIENT_ID)
        m = hashlib.md5()
        m.update(self.config_string.encode(constants.TEXT_ENCODING))
        self.md5sum = m.hexdigest()

    def run(self, archive_dir=None):
        """Write INI to a file of the form $ARCHIVE_DIR/$PATIENT_INI/$CHECKSUM/${PATIENT_ID}.ini"""
        if not archive_dir:
            archive_dir = self.config.get(ini.SETTINGS, ini.ARCHIVE_DIR)
        path_validator().validate_output_dir(archive_dir)
        out_dir_0 = os.path.join(archive_dir, self.patient_id)
        if not os.path.exists(out_dir_0):
            os.mkdir(out_dir_0)
        out_dir_1 = os.path.join(out_dir_0, self.md5sum)
        out_path = None
        if os.path.exists(out_dir_1):
            msg = "Output directory {0} exists; an identical file has already been archived; not writing to archive".format(out_dir_1)
            self.logger.warning(msg)
        else:
            os.mkdir(out_dir_1)
            out_path = os.path.join(out_dir_1, "{0}.ini".format(self.patient_id))
            with open(out_path, 'w') as out_file:
                out_file.write(self.config_string)
            self.logger.info("Archived INI file to {0}".format(out_path))
        return out_path
