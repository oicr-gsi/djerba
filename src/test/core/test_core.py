#! /usr/bin/env python3

import hashlib
import io
import json
import jsonschema
import logging
import os
import re
import tempfile
import time
import unittest
import djerba.util.ini_fields as ini

from configparser import ConfigParser

from djerba.core.configure import config_wrapper, DjerbaConfigError
from djerba.core.ini_generator import ini_generator
from djerba.core.json_validator import plugin_json_validator
from djerba.core.loaders import plugin_loader
from djerba.core.main import main, arg_processor
from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.testing.tools import TestBase
from djerba.util.validator import path_validator
import djerba.core.constants as core_constants
import djerba.util.constants as constants

class TestCore(TestBase):

    LOREM_FILENAME = 'lorem.txt'
    SIMPLE_REPORT_JSON = 'simple_report_expected.json'
    SIMPLE_REPORT_MD5 = '66bf99e6ebe64d89bef09184953fd630'
    SIMPLE_CONFIG_MD5 = 'c9130836e3ca5052383dc3e5b3844000'

    def setUp(self):
        super().setUp() # includes tmp_dir
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))

    def assertSimpleJSON(self, json_path):
        json_expected = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        with open(json_expected) as json_file:
            data_expected = json.loads(json_file.read())
        with open(json_path) as json_file:
            data_found = json.loads(json_file.read())
        self.assertEqual(data_found, data_expected)

    def assertSimpleReport(self, json_path, html_path):
        self.assertSimpleJSON(json_path)
        with open(html_path) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, self.SIMPLE_REPORT_MD5)

    def load_demo1_plugin(self):
        loader = plugin_loader(log_level=logging.WARNING)
        plugin = loader.load('demo1', workspace(self.tmp_dir))
        return plugin

    def read_demo1_config(self, plugin):
        ini_path = os.path.join(self.test_source_dir, 'config_demo1.ini')
        config = ConfigParser()
        config.read(ini_path)
        config = plugin.apply_defaults(config)
        return config

class TestArgs(TestCore):

    class mock_args:
        """Use instead of argparse to store params for testing"""

        def __init__(self, mode, work_dir, ini, ini_out, json, html, pdf):
            self.subparser_name = mode
            self.work_dir = work_dir
            self.ini = ini
            self.ini_out = ini_out
            self.json = json
            self.html = html
            self.pdf = pdf
            self.no_archive = True
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True

    def test_processor(self):
        mode = 'report'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        out_path = os.path.join(self.tmp_dir, 'test_out.ini')
        json = os.path.join(self.tmp_dir, 'test.json')
        html = os.path.join(self.tmp_dir, 'test.html')
        pdf = os.path.join(self.tmp_dir, 'test.pdf')
        args = self.mock_args(mode, work_dir, ini_path, out_path, json, html, pdf)
        ap = arg_processor(args)
        self.assertEqual(ap.get_mode(), mode)
        self.assertEqual(ap.get_ini_path(), ini_path)
        self.assertEqual(ap.get_ini_out_path(), out_path)
        self.assertEqual(ap.get_json_path(), json)
        self.assertEqual(ap.get_html_path(), html)
        self.assertEqual(ap.get_pdf_path(), pdf)
        self.assertEqual(ap.get_log_level(), logging.ERROR)
        self.assertEqual(ap.get_log_path(), None)

    def test_configure(self):
        # run from args, with same inputs as TestSimpleReport
        mode = 'configure'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        out_path = os.path.join(self.tmp_dir, 'config_out.ini')
        json_path = None
        html = None
        pdf = None
        args = self.mock_args(mode, work_dir, ini_path, out_path, json_path, html, pdf)
        main(work_dir, log_level=logging.WARNING).run(args)
        self.assertEqual(self.getMD5(out_path), self.SIMPLE_CONFIG_MD5)

    def test_extract(self):
        # run from args, with same inputs as TestSimpleReport
        mode = 'extract'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config_full.ini')
        out_path = None
        json_path = os.path.join(self.tmp_dir, 'djerba.json')
        html = None
        pdf = None
        args = self.mock_args(mode, work_dir, ini_path, out_path, json_path, html, pdf)
        main(work_dir, log_level=logging.WARNING).run(args)
        self.assertSimpleJSON(json_path)

    def test_render(self):
        # run from args, with same inputs as TestSimpleReport
        mode = 'html'
        work_dir = self.tmp_dir
        ini_path = None
        out_path = None
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        html = os.path.join(self.tmp_dir, 'djerba.html')
        pdf = None
        args = self.mock_args(mode, work_dir, ini_path, out_path, json_path, html, pdf)
        main(work_dir, log_level=logging.WARNING).run(args)
        with open(html) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, self.SIMPLE_REPORT_MD5)

    def test_report(self):
        # run from args, with same inputs as TestSimpleReport
        mode = 'report'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        out_path = None
        json_path = os.path.join(self.tmp_dir, 'test.json')
        html = os.path.join(self.tmp_dir, 'test.html')
        pdf = None
        args = self.mock_args(mode, work_dir, ini_path, out_path, json_path, html, pdf)
        main(work_dir, log_level=logging.WARNING).run(args)
        self.assertSimpleReport(json_path, html)

class TestConfigExpected(TestCore):
    """Test generation of an expected config file"""

    def test_plugin(self):
        """Test config generation for a single plugin"""
        plugin = self.load_demo1_plugin()
        config = plugin.get_expected_config()
        ini_path_found = os.path.join(self.tmp_dir, 'test.ini')
        with open(ini_path_found, 'w') as out_file:
            config.write(out_file)
        ini_path_expected = os.path.join(self.test_source_dir, 'config_demo1_expected.ini')
        with open(ini_path_found) as in_file_1, open(ini_path_expected) as in_file_2:
            self.assertEqual(in_file_1.read(), in_file_2.read())

class TestConfigValidation(TestCore):
    """Test the methods to validate required/optional INI params"""

    def test_simple(self):
        plugin = self.load_demo1_plugin()
        config = self.read_demo1_config(plugin)
        # test a simple plugin
        self.assertTrue(plugin.validate_minimal_config(config))
        with self.assertLogs('djerba.core.configure', level=logging.DEBUG) as log_context:
            self.assertTrue(plugin.validate_full_config(config))
        msg = 'DEBUG:djerba.core.configure:'+\
            '7 expected INI param(s) found for component demo1'
        self.assertIn(msg, log_context.output)

    def test_optional(self):
        plugin = self.load_demo1_plugin()
        config = self.read_demo1_config(plugin)
        # add an optional INI parameter 'foo' with a default value
        # existing config satistifes minimal requirements, but not full specification
        plugin.set_ini_default('foo', 'snark')
        self.assertTrue(plugin.validate_minimal_config(config))
        plugin.set_log_level(logging.CRITICAL)
        with self.assertRaises(DjerbaConfigError):
            plugin.validate_full_config(config)
        plugin.set_log_level(logging.WARNING)
        config = plugin.apply_defaults(config)
        self.assertEqual(config.get('demo1', 'foo'), 'snark')
        # now apply a new config with a different value the 'foo' parameter
        # configured value takes precedence over the default
        config_2 = self.read_demo1_config(plugin)
        config_2.set('demo1', 'foo', 'boojum')
        config_2 = plugin.apply_defaults(config_2)
        self.assertEqual(config_2.get('demo1', 'foo'), 'boojum')
        # test setting all defaults
        config_3 = self.read_demo1_config(plugin)
        defaults = {
            'baz': 'green',
            'fiz': 'purple'
        }
        plugin.set_all_ini_defaults(defaults)
        config_3 = plugin.apply_defaults(config_3)
        self.assertEqual(config_3.get('demo1', 'baz'), 'green')
        self.assertEqual(config_3.get('demo1', 'fiz'), 'purple')

    def test_required(self):
        plugin = self.load_demo1_plugin()
        config = self.read_demo1_config(plugin)
        # add a required INI parameter 'foo' which has not been configured
        plugin.add_ini_required('foo')
        plugin.set_log_level(logging.CRITICAL)
        with self.assertRaises(DjerbaConfigError):
            plugin.validate_minimal_config(config)
        with self.assertRaises(DjerbaConfigError):
            plugin.validate_full_config(config)
        plugin.set_log_level(logging.WARNING)
        # now give foo a config value
        config.set('demo1', 'foo', 'snark')
        self.assertTrue(plugin.validate_minimal_config(config))
        with self.assertLogs('djerba.core.configure', level=logging.DEBUG) as log_context:
            self.assertTrue(plugin.validate_full_config(config))
        msg = 'DEBUG:djerba.core.configure:'+\
            '8 expected INI param(s) found for component demo1'
        self.assertIn(msg, log_context.output)
        # test setting all requirements
        plugin.set_all_ini_required(['foo', 'bar'])
        plugin.set_log_level(logging.CRITICAL)
        with self.assertRaises(DjerbaConfigError):
            plugin.validate_minimal_config(config)
        with self.assertRaises(DjerbaConfigError):
            plugin.validate_full_config(config)
        plugin.set_log_level(logging.CRITICAL)
        config_new = self.read_demo1_config(plugin)
        config_new.set('demo1', 'foo', 'boojum')
        config_new.set('demo1', 'bar', 'jabberwock')
        self.assertTrue(plugin.validate_minimal_config(config_new))
        self.assertTrue(plugin.validate_full_config(config_new))

class TestConfigWrapper(TestCore):

    def test_get_set_has(self):
        cp = ConfigParser()
        cp.read(os.path.join(self.test_source_dir, 'config_full.ini'))
        cw = config_wrapper(cp, 'demo1')
        self.assertEqual(cw.get_core_string('comment'), 'Djerba 1.0 under development')
        self.assertTrue(cw.get_my_boolean('clinical'))
        self.assertFalse(cw.get_my_boolean('supplementary'))
        self.assertEqual(cw.get_my_int('configure_priority'), 100)
        self.assertTrue(cw.has_my_param('question'))
        self.assertFalse(cw.has_my_param('noodles'))
        cw.set_my_param('lunch', 'sushi')
        config_1 = cw.get_config()
        self.assertTrue(config_1.get('demo1', 'lunch'), 'sushi')
        cw.set_my_priorities(42)
        for key in [
            core_constants.CONFIGURE_PRIORITY,
            core_constants.EXTRACT_PRIORITY,
            core_constants.RENDER_PRIORITY
        ]:
            self.assertEqual(cw.get_my_int(key), 42)
        self.assertTrue(cw.get_boolean('demo2', 'clinical'))
        self.assertFalse(cw.get_boolean('demo2', 'supplementary'))
        self.assertEqual(cw.get_int('demo2', 'configure_priority'), 200)
        self.assertTrue(cw.has_param('demo2', 'demo2_param'))
        self.assertFalse(cw.has_param('demo2', 'noodles'))
        cw.set_param('demo2', 'dinner', 'pizza')
        config_2 = cw.get_config()
        self.assertTrue(config_2.get('demo2', 'dinner'), 'pizza')

    def test_env_templates(self):
        data_dir_orig = os.environ.get(core_constants.DJERBA_DATA_DIR_VAR)
        os.environ[core_constants.DJERBA_DATA_DIR_VAR] = self.tmp_dir
        config = ConfigParser()
        config.read(os.path.join(self.test_source_dir, 'config_demo1.ini'))
        wrapper = config_wrapper(config, 'demo1')
        wrapper.apply_my_env_templates()
        expected = '{0}/not/a/file.txt'.format(self.tmp_dir)
        self.assertEqual(wrapper.get_my_string('dummy_file'), expected)
        if data_dir_orig != None:
            os.environ[core_constants.DJERBA_DATA_DIR_VAR] = data_dir_orig



class TestIniGenerator(TestCore):
    """Test the INI generator"""

    COMPONENT_NAMES = [
        'demo1',
        'demo2',
        'provenance_helper',
        'gene_information_merger'
    ]

    def test_class(self):
        generator = ini_generator(log_level=logging.WARNING)
        generated_ini_path = os.path.join(self.tmp_dir, 'generated.ini')
        names = ['core']
        names.extend(self.COMPONENT_NAMES)
        generator.write_config(names, generated_ini_path)
        self.assertTrue(os.path.exists(generated_ini_path))
        expected_ini_path = os.path.join(self.test_source_dir, 'generated.ini')
        with open(generated_ini_path) as in_file_1, open(expected_ini_path) as in_file_2:
            self.assertEqual(in_file_1.read(), in_file_2.read())

    def test_script(self):
        #out_path = os.path.join(self.tmp_dir, 'generated.ini')
        out_path = os.path.join('/home/ibancarz/tmp', 'generated.ini')
        cmd = ['generate_ini.py', '--out', out_path]
        cmd.extend(self.COMPONENT_NAMES)
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        expected_ini_path = os.path.join(self.test_source_dir, 'generated.ini')
        with open(out_path) as in_file_1, open(expected_ini_path) as in_file_2:
            self.assertEqual(in_file_1.read(), in_file_2.read())


class TestMainScript(TestCore):
    """Test the main djerba.py script"""

    def test_configure_cli(self):
        mode = 'configure'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        out_path = os.path.join(self.tmp_dir, 'config_out.ini')
        cmd = [
            'djerba.py', mode,
            '--work-dir', work_dir,
            '--ini', ini_path,
            '--ini-out', out_path,
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.getMD5(out_path), self.SIMPLE_CONFIG_MD5)

    def test_extract_cli(self):
        mode = 'extract'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config_full.ini')
        json_path = os.path.join(self.tmp_dir, 'test.json')
        cmd = [
            'djerba.py', mode,
            '--work-dir', work_dir,
            '--ini', ini_path,
            '--json', json_path,
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assertSimpleJSON(json_path)

    def test_render_cli(self):
        mode = 'html'
        work_dir = self.tmp_dir
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        html_path = os.path.join(self.tmp_dir, 'djerba.html')
        cmd = [
            'djerba.py', mode,
            '--json', json_path,
            '--html', html_path
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        with open(html_path) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, self.SIMPLE_REPORT_MD5)

    def test_report_cli(self):
        mode = 'report'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        json_path = os.path.join(self.tmp_dir, 'test.json')
        html = os.path.join(self.tmp_dir, 'test.html')
        cmd = [
            'djerba.py', mode,
            '--work-dir', work_dir,
            '--ini', ini_path,
            '--json', json_path,
            '--html', html
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assertSimpleReport(json_path, html)

class TestModuleDir(TestCore):

    def test(self):
        plugin = self.load_demo1_plugin()
        module_dir = plugin.get_module_dir()
        self.assertTrue(os.path.exists(module_dir))
        self.assertTrue(os.path.isdir(module_dir))
        self.assertTrue(os.path.isfile(os.path.join(module_dir, 'plugin.py')))

class TestPriority(TestCore):
    """Test controlling the configure/extract/render order with priority levels"""

    def find_line_position(self, doc, target):
        # input is a 'document' (string of one or more lines)
        # find position of first line containing given string, if any
        # if not found, return 0
        position = 0
        for line in re.split('\n', doc):
            position += 1
            if target in line:
                break
        return position

    def test_configure_priority(self):
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        djerba_main = main(self.tmp_dir, log_level=logging.WARNING)
        with self.assertLogs('djerba.core.main', level=logging.DEBUG) as log_context:
            config = djerba_main.configure(ini_path)
        names_and_orders = [
            ['core', 1],
            ['demo1', 2],
            ['demo2', 3],
            ['gene_information_merger', 4]
        ]
        prefix = 'DEBUG:djerba.core.main:'
        template = '{0}Configuring component {1} in order {2}'
        for (name, order) in names_and_orders:
            msg = template.format(prefix, name, order)
            self.assertIn(msg, log_context.output)
        # now give demo2 a higher priority than demo1
        config.set('demo1', core_constants.CONFIGURE_PRIORITY, '300')
        config.set('demo2', core_constants.CONFIGURE_PRIORITY, '200')
        ini_path_2 = os.path.join(self.tmp_dir, 'config_modified.ini')
        with open(ini_path_2, 'w') as out_file:
            config.write(out_file)
        with self.assertLogs('djerba.core.main', level=logging.DEBUG) as log_context:
            djerba_main.configure(ini_path_2)
        names_and_orders = [
            ['core', 1],
            ['demo2', 2], # <---- changed order
            ['demo1', 3],
            ['gene_information_merger', 4]
        ]
        for (name, order) in names_and_orders:
            msg = template.format(prefix, name, order)
            self.assertIn(msg, log_context.output)

    def test_extract_priority(self):
        # core and merger do not have extract steps
        ini_path = os.path.join(self.test_source_dir, 'config_full.ini')
        djerba_main = main(self.tmp_dir, log_level=logging.WARNING)
        config = ConfigParser()
        config.read(ini_path)
        with self.assertLogs('djerba.core.main', level=logging.DEBUG) as log_context:
            djerba_main.extract(config)
        names_and_orders = [
            ['demo1', 1],
            ['demo2', 2],
        ]
        prefix = 'DEBUG:djerba.core.main:'
        template = '{0}Extracting component {1} in order {2}'
        for (name, order) in names_and_orders:
            msg = template.format(prefix, name, order)
            self.assertIn(msg, log_context.output)
        # now give demo2 a higher priority than demo1
        config.set('demo1', core_constants.EXTRACT_PRIORITY, '300')
        config.set('demo2', core_constants.EXTRACT_PRIORITY, '200')
        with self.assertLogs('djerba.core.main', level=logging.DEBUG) as log_context:
            djerba_main.extract(config)
        names_and_orders = [
            ['demo2', 1], # <---- changed order
            ['demo1', 2],
        ]
        for (name, order) in names_and_orders:
            msg = template.format(prefix, name, order)
            self.assertIn(msg, log_context.output)

    def test_render_priority(self):
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        djerba_main = main(self.tmp_dir, log_level=logging.WARNING)
        with open(json_path) as json_file:
            data = json.loads(json_file.read())
        html = djerba_main.render(data)
        pos1 = self.find_line_position(html, 'demo1')
        pos2 = self.find_line_position(html, 'The Question') # demo2 output
        self.assertNotEqual(0, pos1)
        self.assertNotEqual(0, pos2)
        self.assertTrue(pos1 < pos2)
        # now give demo2 a higher priority than demo1
        data['plugins']['demo1']['priorities']['render'] = 200
        data['plugins']['demo2']['priorities']['render'] = 100
        html = djerba_main.render(data)
        pos1 = self.find_line_position(html, 'demo1')
        pos2 = self.find_line_position(html, 'The Question') # demo2 output
        self.assertNotEqual(0, pos1)
        self.assertNotEqual(0, pos2)
        self.assertTrue(pos1 > pos2) # <---- changed order

class TestSimpleReport(TestCore):

    def test_report(self):
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        djerba_main = main(self.tmp_dir, log_level=logging.WARNING)
        config = djerba_main.configure(ini_path)
        data_found = djerba_main.extract(config)
        with open(json_path) as json_file:
            data_expected = json.loads(json_file.read())
        self.assertEqual(data_found, data_expected)
        html = djerba_main.render(data_found)
        self.assert_report_MD5(html, self.SIMPLE_REPORT_MD5)

class TestJSONValidator(TestCore):

    EXAMPLE_DEFAULT = 'plugin_example.json'
    EXAMPLE_EMPTY = 'plugin_example_empty.json'
    EXAMPLE_BROKEN = 'plugin_example_broken.json'

    def run_script(self, in_path):
        runner = subprocess_runner(log_level=logging.CRITICAL)
        with open(in_path) as in_file:
            input_string = in_file.read()
        result = runner.run(['validate_plugin_json.py'], stdin=input_string, raise_err=False)
        return result.returncode

    def test_plugin(self):
        validator = plugin_json_validator(log_level=logging.WARNING)
        for filename in [self.EXAMPLE_DEFAULT, self.EXAMPLE_EMPTY]:
            in_path = os.path.join(self.test_source_dir, filename)
            with open(in_path) as in_file:
                input_data = json.loads(in_file.read())
            self.assertTrue(validator.validate_data(input_data))

    def test_plugin_broken(self):
        validator = plugin_json_validator(log_level=logging.CRITICAL)
        in_path = os.path.join(self.test_source_dir, self.EXAMPLE_BROKEN)
        with open(in_path) as in_file:
            input_data = json.loads(in_file.read())
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validator.validate_data(input_data)

    def test_script(self):
        good_path = os.path.join(self.test_source_dir, self.EXAMPLE_DEFAULT)
        self.assertEqual(self.run_script(good_path), 0)
        # complete report JSON doesn't (and shouldn't) satisfy the plugin schema
        bad_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        self.assertEqual(self.run_script(bad_path), 3)

class TestWorkspace(TestCore):

    def test(self):
        gzip_filename = 'lorem.gz'
        with open(os.path.join(self.test_source_dir, self.LOREM_FILENAME)) as in_file:
            lorem = in_file.read()
        ws = workspace(self.tmp_dir)
        ws_silent = workspace(self.tmp_dir, log_level=logging.CRITICAL)
        # test if we can write a file
        ws.write_string(self.LOREM_FILENAME, lorem)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, self.LOREM_FILENAME)))
        # test if we can read the file
        ws_lorem = ws.read_string(self.LOREM_FILENAME)
        self.assertEqual(ws_lorem, lorem)
        # test if reading a nonexistent file breaks
        with self.assertRaises(OSError):
            ws_silent.read_string('/dummy/file/path')
        # test if we can open the file
        with ws.open_file('lorem.txt') as demo_file:
            self.assertTrue(isinstance(demo_file, io.TextIOBase))
        # test if opening a nonexistent file breaks
        with self.assertRaises(OSError):
            ws_silent.open_file('/dummy/file/path')
        # test gzip I/O
        with ws.open_gzip_file(gzip_filename, write=True) as gzip_file:
            gzip_file.write(lorem)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, gzip_filename)))
        with ws.open_gzip_file(gzip_filename) as gzip_file:
            lorem_from_gzip = gzip_file.read()
        self.assertEqual(lorem_from_gzip, lorem)


if __name__ == '__main__':
    unittest.main()
