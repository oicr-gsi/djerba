"""Run Djerba, eg. on the command line"""

import configparser
import json
import os
import djerba.constants as constants
import djerba.ini_fields as ini
from djerba.configure.configure import config_updater
from djerba.extract.extractor import extractor
from djerba.build.reader import multiple_reader

class runner:

    def __init__(self, config):
        self.config = config
        self.bedPath = config[ini.SETTINGS][ini.BED_PATH]
        self.workDir = config[ini.SETTINGS][ini.SCRATCH_DIR]
        self.donor = config[ini.INPUTS][ini.PATIENT]
        self.gamma = config[ini.INPUTS].getint(ini.GAMMA)
        self.project = config[ini.INPUTS][ini.STUDY_ID]
        self.provenancePath = config[ini.SETTINGS][ini.PROVENANCE]
        outdir = config[ini.INPUTS][ini.OUT_DIR]
        self.outPath = os.path.join(outdir, config[ini.SETTINGS][ini.METRICS_FILENAME])
        schemaPath = config[ini.SETTINGS][ini.METRICS_SCHEMA]
        with open(schemaPath) as f:
            self.schema = json.loads(f.read())
        self.require_complete = config[ini.SETTINGS].getboolean(ini.REQUIRE_COMPLETE)
        self.validate = config[ini.SETTINGS].getboolean(ini.VALIDATE)

    def run(self):
        """Configure extraction; extract data, collate & write as JSON"""
        updater = config_updater(self.config)
        updater.update()
        self.config = updater.get_config()
        ext = extractor(self.config)
        ext.run()
        components = []
        for componentPath in ext.getComponentPaths():
            with open(componentPath) as f:
                components.append(json.loads(f.read()))
        reader = multiple_reader(components, self.schema)
        with open(self.outPath, 'w') as out:
            output = reader.get_output(self.require_complete, self.validate)
            out.write(json.dumps(output, sort_keys=True, indent=4))

