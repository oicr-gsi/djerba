#! /usr/bin/env python3

import os
import json
import logging
import unittest
import tempfile
from configparser import ConfigParser
from shutil import copy

import djerba.core.constants as constants
from djerba.plugins.plugin_tester import PluginTester
from djerba.plugins.benchmark.plugin import main as BenchmarkPlugin
from djerba.util.environment import directory_finder
from djerba.util.validator import path_validator

class TestBenchmark(PluginTester):

    PLACEHOLDER = 'PLACEHOLDER'

    def setUp(self):
        self.path_validator = path_validator()
        self.maxDiff = None
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_')
        self.tmp_dir = self.tmp.name
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))

    def testBenchmark(self):
        json_location = os.path.join(self.test_source_dir, "benchmark.json")
        data_dir_root = directory_finder().get_test_dir()
        data_dir = os.path.join(data_dir_root, 'plugins', 'benchmark')
        params = {
            self.INI: self.write_ini_file(data_dir),
            self.JSON: json_location,
            self.MD5: '908399d7bbadbd7192ca331c77d41835'
        }
        self.run_basic_test(self.test_source_dir, params)

    def redact_json_data(self, data):
        results = data['results']
        redacted_donor_results = []
        for k,v in results.items():
            if k == 'donor_results':
                for donor_result in v:
                    for k2,v2 in donor_result.items():
                        if k2 in ['input_file', 'ref_file']:
                            file_name = os.path.basename(v2)
                            donor_result[k2] = os.path.join(self.PLACEHOLDER, file_name)
                    redacted_donor_results.append(donor_result)
            elif k=='run_time':
                results[k] = self.PLACEHOLDER
            elif k=='input_name':
                results[k] = 'Unknown'
        results['donor_results'] = redacted_donor_results
        data['results'] = results
        return data

    def write_ini_file(self, data_dir):
        # write input/ref JSON on the fly, using individual report JSONs in data dir
        names = ['GSICAPBENCH_1248_WGTS', 'GSICAPBENCH_1309_WGTS']
        inputs = {}
        refs = {}
        for name in names:
            inputs[name] = os.path.join(data_dir, name+'_report.json')
            refs[name] = os.path.join(data_dir, name+'_report.json')
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
        private_dir = directory_finder().get_private_dir()
        ref_dir = os.path.join(private_dir, 'benchmarking', 'djerba_bench_reference')
        cp.set('benchmark', BenchmarkPlugin.REF_DIR, ref_dir)
        ini_path = os.path.join(self.tmp_dir, 'benchmark.ini')
        with open(ini_path, 'w') as ini_file:
            cp.write(ini_file)
        return ini_path

if __name__ == '__main__':
    unittest.main()
