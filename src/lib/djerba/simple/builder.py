"""Scan files/directories to locate inputs and build configuration for reader objects"""

import json

class builder:

    """Build configuration for readers"""

    def __init__(self, analysis_unit):
        self.analysis_unit = analysis_unit

    def build(self):
        """Build all configuration objects"""
        configs = []
        return configs

    def build_json(self, input_paths):
        """Build config for json readers, by simply reading the config files"""
        configs = []
        for input_path in input_paths:
            with open(input_path) as f:
                configs.append(json.loads(f.read()))
        return configs

    def build_mastersheet(self, mastersheet_path):
        """Build config for a mastersheet reader"""
        config = {
            "analysis_unit": self.analysis_unit,
            "mastersheet_path": mastersheet_path,
            "reader_class": "mastersheet_reader"
        }
        return config
