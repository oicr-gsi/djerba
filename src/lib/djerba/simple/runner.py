"""Run Djerba, eg. on the command line"""

import configparser
import json
import os
import djerba.simple.constants as constants
from djerba.simple.discover.discover import extraction_config
from djerba.simple.extract.extractor import extractor
from djerba.simple.build.reader import multiple_reader

class runner:

    def __init__(self, provenance, project, donor, bedPath, iniPath, workDir, outPath, schemaPath,
                 rScriptDir,
                 gamma=None, overwrite=False, require_complete=False, validate=False):
        # validate the iniPath
        if not os.path.exists(iniPath):
            raise OSError("Input path %s does not exist" % iniPath)
        elif not os.path.isfile(iniPath):
            raise OSError("Input path %s is not a file" % iniPath)
        elif not os.access(iniPath, os.R_OK):
            raise OSError("Input path %s is not readable" % iniPath)
        self.iniPath = iniPath
        # validate the working directory
        if not os.path.exists(workDir):
            raise OSError("Output path %s does not exist" % workDir)
        elif not os.path.isdir(workDir):
            raise OSError("Output path %s is not a directory" % workDir)
        elif not os.access(workDir, os.W_OK):
            raise OSError("Output path %s is not writable" % workDir)
        elif len(os.listdir(workDir)) > 0 and not overwrite:
            raise OSError("Output path %s is not empty; overwrite mode is not in effect" % workDir)
        self.workDir = workDir
        # TODO confirm outPath is writable
        self.outPath = outPath
        # TODO confirm schemaPath, provenance, bedPath are readable
        with open(schemaPath) as f:
            self.schema = json.loads(f.read())
        self.provenancePath = provenance
        self.project = project
        self.rScriptDir = rScriptDir
        self.donor = donor
        self.gamma = gamma
        self.bedPath = bedPath
        self.require_complete = require_complete
        self.validate = validate

    def read_bare_ini(self, iniPath):
        """Read a 'bare' INI file without section headers; return its single section as a dictionary"""
        header = 'foo'
        with open(iniPath) as iniFile:
            # prepend header required by configparser
            configString = "[%s]\n%s" % (header, iniFile.read())
        parser = configparser.ConfigParser()
        parser.read_string(configString)
        return dict(parser[header])

    def run(self):
        """Get params from provenance; update with INI parameters; extract data, collate & write as JSON"""
        # Eventually, we want to get all params from provenance/filesystem without a supplementary INI
        config = extraction_config(self.provenancePath, self.project, self.donor, self.gamma)
        config.update(self.read_bare_ini(self.iniPath))
        ext = extractor(config.get_params(), self.bedPath, self.workDir, self.rScriptDir)
        ext.run()
        components = []
        for componentPath in ext.getComponentPaths():
            with open(componentPath) as f:
                components.append(json.loads(f.read()))
        reader = multiple_reader(components, self.schema)
        with open(self.outPath, 'w') as out:
            output = reader.get_output(self.require_complete, self.validate)
            out.write(json.dumps(output, sort_keys=True, indent=4))

