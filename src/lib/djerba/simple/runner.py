"""Run Djerba, eg. on the command line"""

import json
import os
from djerba.simple.preprocess.processor import processor
from djerba.simple.build.reader import multiple_reader

class runner:

    def __init__(self, iniPath, workDir, outPath, schemaPath,
                 overwrite=False, require_complete=False, validate=False):
        # TODO replace iniPath with a "find" step to discover/link input data
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
        # TODO confirm schemaPath is readable
        with open(schemaPath) as f:
            self.schema = json.loads(f.read())
        self.require_complete = require_complete
        self.validate = validate

    def run(self):
        preprocessor = processor(self.iniPath, self.workDir)
        preprocessor.run()
        configs = []
        for configPath in preprocessor.getConfigPaths():
            with open(configPath) as f:
                configs.append(json.loads(f.read()))
        reader = multiple_reader(configs, self.schema)
        with open(self.outPath, 'w') as out:
            output = reader.get_output(self.require_complete, self.validate)
            out.write(json.dumps(output, sort_keys=True, indent=4))

