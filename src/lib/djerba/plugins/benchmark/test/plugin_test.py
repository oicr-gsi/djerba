#! /usr/bin/env python3

import os
import json
import logging
import unittest
import tempfile
import djerba.core.constants as constants
from configparser import ConfigParser
from djerba.plugins.plugin_tester import PluginTester
from djerba.plugins.benchmark.plugin import main as BenchmarkPlugin
from djerba.util.environment import directory_finder
from djerba.util.validator import path_validator

class TestBenchmark(PluginTester):

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name

    def testBenchmark(self):
        self.tmp_dir = '/u/ibancarz/workspace/djerba/test_20240821_01'
        data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(data_dir_root, 'plugins', 'benchmark')
        test_source_dir = os.path.realpath(os.path.dirname(__file__))
        json_location = os.path.join(test_source_dir, "benchmark.json")
        data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(data_dir_root, 'plugins', 'benchmark')
        params = {
            self.INI: self.write_ini_file(data_dir),
            self.JSON: json_location,
            self.MD5: '858a5524cf16265e70d069d65b2b18b0'
        }
        self.run_basic_test(test_source_dir, params)

    def redact_json_data(self, data):
        for k,v in data.items():
            if k in ['input_file', 'ref_file']:
                file_name = os.path.basename(v)
                data[k] = os.path.join('PLACEHOLDER', file_name)
        return data

    def write_ini_file(self, data_dir):
        # write input/ref JSON on the fly, using individual report JSONs in data dir
        donors = ['GSICAPBENCH_1219', 'GSICAPBENCH_1232']
        inputs = {}
        refs = {}
        for donor in donors:
            inputs[donor] = os.path.join(data_dir, donor+'_input.json')
            refs[donor] = os.path.join(data_dir, donor+'_reference.json')
        input_path = os.path.join(self.tmp_dir, 'inputs.json')
        with open(input_path, 'w') as input_file:
            input_file.write(json.dumps(inputs))
        ref_path = os.path.join(self.tmp_dir, 'reference.json')
        with open(ref_path, 'w') as ref_file:
            ref_file.write(json.dumps(refs))
        cp = ConfigParser()
        cp.add_section('core')
        cp.add_section('benchmark')
        cp.set('benchmark', BenchmarkPlugin.INPUT_FILE, input_path)
        cp.set('benchmark', BenchmarkPlugin.REF_FILE, ref_path)
        ini_path = os.path.join(self.tmp_dir, 'benchmark.ini')
        with open(ini_path, 'w') as ini_file:
            cp.write(ini_file)
        return ini_path

if __name__ == '__main__':
    unittest.main()
