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
from copy import copy
from glob import glob
from string import Template

from djerba.core.configure import config_wrapper, core_configurer, DjerbaConfigError
from djerba.core.html_cache import html_cache, DjerbaHtmlCacheError
from djerba.core.ini_generator import ini_generator
from djerba.core.json_validator import plugin_json_validator
from djerba.core.loaders import plugin_loader, core_config_loader, DjerbaLoadError
from djerba.core.main import main, arg_processor, DjerbaDependencyError, DjerbaHtmlCacheError
from djerba.core.workspace import workspace
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.testing.tools import TestBase
from djerba.util.validator import path_validator
import djerba.core.constants as core_constants
import djerba.plugins.base
import djerba.util.constants as constants

class TestCore(TestBase):

    LOREM_FILENAME = 'lorem.txt'
    SIMPLE_REPORT_JSON = 'simple_report_expected.json'
    SIMPLE_REPORT_UPDATE_JSON = 'simple_report_for_update.json'
    SIMPLE_REPORT_UPDATE_FAILED_JSON = 'simple_report_for_update_failed.json'
    SIMPLE_CONFIG_MD5 = '2311145c9d6782334c05816058d3623f'
    SIMPLE_REPORT_MD5 = '7afa81bc29e86af6a23830ece99674b0'

    class mock_args:
        """Use instead of argparse to store params for testing"""

        def __init__(self, mode, work_dir, ini, ini_out, json, out_dir, pdf):
            self.subparser_name = mode
            self.work_dir = work_dir
            self.ini = ini
            self.ini_out = ini_out
            self.json = json
            self.out_dir = out_dir
            self.no_archive = True
            self.pdf = pdf
            # logging
            self.log_path = None
            self.debug = False
            self.verbose = False
            self.quiet = True
    
    def setUp(self):
        super().setUp() # includes tmp_dir
        self.test_source_dir = os.path.realpath(os.path.dirname(__file__))

    def assertSimpleJSON(self, json_path):
        json_expected = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        with open(json_expected) as json_file:
            data_expected = json.loads(json_file.read())
        with open(json_path) as json_file:
            data_found = json.loads(json_file.read())
            data_found['core']['extract_time'] = '2024-01-01_12:00:00 -0500'
            data_found['core']['core_version'] = 'placeholder'
            data_found['html_cache']['placeholder_report.clinical'] = 'placeholder'
        self.assertEqual(data_expected, data_found)

    def assertSimpleReport(self, json_path, html_path):
        self.assertSimpleJSON(json_path)
        with open(html_path) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, self.SIMPLE_REPORT_MD5)

    def load_demo1_plugin(self):
        loader = plugin_loader(log_level=logging.WARNING)
        plugin = loader.load('demo1', workspace(self.tmp_dir))
        return plugin

    def read_demo1_config(self, plugin, filename='config_demo1.ini'):
        ini_path = os.path.join(self.test_source_dir, filename)
        config = ConfigParser()
        config.read(ini_path)
        config = plugin.apply_defaults(config)
        return config

class TestArgs(TestCore):

    def test_processor(self):
        mode = 'report'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        out_path = os.path.join(self.tmp_dir, 'test_out.ini')
        pdf = os.path.join(self.tmp_dir, 'test.pdf')
        args = self.mock_args(mode, work_dir, ini_path, out_path, json, self.tmp_dir, False)
        ap = arg_processor(args)
        self.assertEqual(ap.get_mode(), mode)
        self.assertEqual(ap.get_ini_path(), ini_path)
        self.assertEqual(ap.get_ini_out_path(), out_path)
        self.assertEqual(ap.get_json(), json)
        self.assertEqual(ap.get_log_level(), logging.ERROR)
        self.assertEqual(ap.get_log_path(), None)

    def test_configure(self):
        # run from args, with same inputs as TestSimpleReport
        mode = 'configure'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        out_path = os.path.join(self.tmp_dir, 'config_out.ini')
        json = None
        args = self.mock_args(mode, work_dir, ini_path, out_path, json, self.tmp_dir, False)
        main(work_dir, log_level=logging.WARNING).run(args)
        self.assertEqual(self.SIMPLE_CONFIG_MD5, self.getMD5(out_path))

    def test_extract(self):
        # run from args, with same inputs as TestSimpleReport
        mode = 'extract'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config_full.ini')
        out_path = None
        json_path = os.path.join(self.tmp_dir, 'djerba.json')
        args = self.mock_args(
            mode, work_dir, ini_path, out_path, json_path, self.tmp_dir, False
        )
        main(work_dir, log_level=logging.WARNING).run(args)
        self.assertSimpleJSON(json_path)

    def test_render(self):
        # run from args, with same inputs as TestSimpleReport
        mode = 'render'
        work_dir = self.tmp_dir
        ini_path = None
        out_path = None
        json = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        args = self.mock_args(mode, work_dir, ini_path, out_path, json, self.tmp_dir, False)
        main(work_dir, log_level=logging.ERROR).run(args)
        filename = 'placeholder_report.clinical.html'
        with open(os.path.join(self.tmp_dir, filename)) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, self.SIMPLE_REPORT_MD5)

    def test_report(self):
        # run from args, with same inputs as TestSimpleReport
        mode = 'report'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        out_path = None
        json = os.path.join(self.tmp_dir, 'placeholder_report.json')
        html = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf = False
        args = self.mock_args(mode, work_dir, ini_path, out_path, json, self.tmp_dir, pdf)
        main(work_dir, log_level=logging.ERROR).run(args)
        self.assertSimpleReport(json, html)

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
    """Test the methods to validate required/optional INI params and attributes"""

    def test_attributes(self):
        plugin = self.load_demo1_plugin()
        config = self.read_demo1_config(plugin)
        attributes = plugin.get_config_wrapper(config).get_my_attributes()
        self.assertTrue(plugin.check_attributes_known(attributes))
        config.set('demo1', 'attributes', 'clinical,awesome')
        attributes = plugin.get_config_wrapper(config).get_my_attributes()
        with self.assertLogs('djerba:demo1', level=logging.WARNING) as log_context:
            self.assertFalse(plugin.check_attributes_known(attributes))
        msg = "WARNING:djerba:demo1:Unknown attribute 'awesome' in config"
        self.assertIn(msg, log_context.output)

    def test_simple(self):
        plugin = self.load_demo1_plugin()
        config = self.read_demo1_config(plugin)
        # test a simple plugin
        self.assertTrue(plugin.validate_minimal_config(config))
        with self.assertLogs('djerba:demo1', level=logging.DEBUG) as log_context:
            self.assertTrue(plugin.validate_full_config(config))
        msg = 'DEBUG:djerba:demo1:'+\
            '8 expected INI param(s) found for component demo1'
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
        for k,v in defaults.items():
            plugin.set_ini_default(k, v)
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
        with self.assertLogs('djerba:demo1', level=logging.DEBUG) as log_context:
            self.assertTrue(plugin.validate_full_config(config))
        msg = 'DEBUG:djerba:demo1:'+\
            '9 expected INI param(s) found for component demo1'
        self.assertIn(msg, log_context.output)
        # test setting all requirements
        plugin.add_ini_required('bar') # 'foo' is already required
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
        self.assertEqual(cw.get_core_string('author'), 'CGI Author')
        self.assertEqual(cw.get_my_int('configure_priority'), 200)
        self.assertTrue(cw.has_my_param('question'))
        self.assertFalse(cw.has_my_param('noodles'))
        cw.set_my_param('lunch', 'sushi')
        config_1 = cw.get_config()
        self.assertTrue(config_1.get('demo1', 'lunch'), 'sushi')
        cw.set_my_param('sushi_is_tasty', True)
        cw.set_my_param('sushi_is_nasty', False)
        self.assertTrue(cw.get_my_boolean('sushi_is_tasty'))
        self.assertFalse(cw.get_my_boolean('sushi_is_nasty'))
        cw.set_my_priorities(42)
        for key in [
            core_constants.CONFIGURE_PRIORITY,
            core_constants.EXTRACT_PRIORITY,
            core_constants.RENDER_PRIORITY
        ]:
            self.assertEqual(cw.get_my_int(key), 42)
        self.assertEqual(cw.get_int('demo2', 'configure_priority'), 300)
        self.assertTrue(cw.has_param('demo2', 'demo2_param'))
        self.assertFalse(cw.has_param('demo2', 'noodles'))
        cw.set_param('demo2', 'dinner', 'pizza')
        config_2 = cw.get_config()
        self.assertTrue(config_2.get('demo2', 'dinner'), 'pizza')


class TestCoreConfigurer(TestCore):
    """Test the 'core_configurer' class"""

    OUTPUT = 'core_config_test.ini'
    TEST_USERNAME = 'test'
    TEST_AUTHOR = 'Test Author'

    def assert_core_config(self, config):
        out_path = os.path.join(self.tmp_dir, self.OUTPUT)
        with open(out_path, 'w') as out_file:
            config.write(out_file)
        with open(out_path) as in_file:
            config_found = in_file.read().strip()
        expected_ini_path = os.path.join(self.test_source_dir, 'core_config_expected.ini')
        with open(expected_ini_path) as in_file:
            config_expected = in_file.read().strip()
        self.assertEqual(config_expected, config_found)

    def run_core_config(self, default_author=True):
        loader = core_config_loader(log_level=logging.WARNING)
        core_configurer = loader.load(workspace(self.tmp_dir))
        config = ConfigParser()
        config.add_section('core')
        if default_author:
            config.set('core', 'author', core_constants.DEFAULT_AUTHOR)
        config = core_configurer.configure(config)
        return config

    def run_core_config_no_author(self):
        return self.run_core_config(default_author=False)

    def test_author(self):
        """Test author lookup"""
        user_orig = os.environ.get('USER')
        sudo_user_orig = os.environ.get('SUDO_USER')
        private_dir_orig = os.environ.get('DJERBA_PRIVATE_DIR')
        # make a temporary lookup file
        os.environ['DJERBA_PRIVATE_DIR'] = self.tmp_dir
        lookup = {
            self.TEST_USERNAME: self.TEST_AUTHOR
        }
        with open(os.path.join(self.tmp_dir, 'djerba_users.json'), 'w') as out_file:
            out_file.write(json.dumps(lookup))
        # unknown username -> default author
        os.environ['USER'] = 'nobody'
        config = self.run_core_config_no_author()
        self.assertEqual(config.get('core', 'author'), core_constants.DEFAULT_AUTHOR)
        # known username -> test author
        os.environ['USER'] = self.TEST_USERNAME
        config = self.run_core_config_no_author()
        self.assertEqual(config.get('core', 'author'), self.TEST_AUTHOR)
        # known sudo username -> test author
        os.environ['USER'] = 'nobody'
        os.environ['SUDO_USER'] = self.TEST_USERNAME
        config = self.run_core_config_no_author()
        self.assertEqual(config.get('core', 'author'), self.TEST_AUTHOR)        
        # put environment variables back as they were
        original = {
            'USER': user_orig,
            'SUDO_USER': sudo_user_orig,
            'DJERBA_PRIVATE_DIR': private_dir_orig
        }
        for k,v in original.items():
            if v != None:
                os.environ[k] = v
            else:
                del os.environ[k]

    def test_default(self):
        """Test default configuration with UUID"""
        config = self.run_core_config()
        expr = 'OICR-CGI-[abcdefgh0-9]{32}'
        self.assertTrue(re.match(expr, config.get('core', 'report_id')))
        config.set('core', 'report_id', 'placeholder')
        self.assert_core_config(config)

    def test_input_params(self):
        """Test configuration with input params file"""
        info = {
            core_constants.REQUISITION_ID: 'foo'
        }
        info_path = os.path.join(self.tmp_dir, core_constants.DEFAULT_INPUT_PARAMS)
        with open(info_path, 'w') as out_file:
            print(json.dumps(info), file=out_file)
        config = self.run_core_config()
        self.assertEqual('foo-v1', config.get('core', 'report_id'))
        config.set('core', 'report_id', 'placeholder')
        self.assert_core_config(config)


class TestDependencies(TestCore):
    """Test the 'depends' parameters"""

    def test_depends_configure(self):
        mode = 'configure'
        work_dir = self.tmp_dir
        ini_path = 'placeholder'
        out_path = os.path.join(self.tmp_dir, 'config_out.ini')
        json_path = None
        html = None
        pdf = None
        args = self.mock_args(mode, work_dir, ini_path, out_path, json_path, html, pdf)
        for num in [1,2,3]:
            filename = 'depends_configure_broken_{0}.ini'.format(num)
            args.ini = os.path.join(self.test_source_dir, filename)
            with self.assertRaises(DjerbaDependencyError):
                main(work_dir, log_level=logging.CRITICAL).run(args)
        args.ini = os.path.join(self.test_source_dir, 'depends_configure.ini')
        main(work_dir, log_level=logging.WARNING).run(args)

    def test_depends_extract(self):
        mode = 'extract'
        work_dir = self.tmp_dir
        ini_path = 'placeholder'
        out_path = None
        json_path = os.path.join(self.tmp_dir, 'djerba.json')
        html = None
        pdf = None
        args = self.mock_args(mode, work_dir, ini_path, out_path, json_path, html, pdf)
        for num in [1,2,3]:
            filename = 'depends_extract_broken_{0}.ini'.format(num)
            args.ini = os.path.join(self.test_source_dir, filename)
            with self.assertRaises(DjerbaDependencyError):
                main(work_dir, log_level=logging.CRITICAL).run(args)
        args.ini = os.path.join(self.test_source_dir, 'depends_extract.ini')
        question_path = os.path.join(self.tmp_dir, 'question.txt')
        with open(question_path, 'w') as out_file:
            out_file.write('What do you get if you multiply six by nine?\n')
        main(work_dir, log_level=logging.WARNING).run(args)
        self.assertTrue(os.path.exists(json_path))

class TestHtmlCache(TestCore):
    """Test the HTML cache"""

    def test_encode_decode(self):
        # test an encoding/decoding round trip
        # including non-Latin characters (Greek alpha, beta, gamma, delta)
        string_to_encode = "Hello, world! \u03b1\u03b2\u03b3\u03b4"
        cache = html_cache(log_level=logging.ERROR)
        encoded = cache.encode_to_base64(string_to_encode)
        decoded_string = cache.decode_from_base64(encoded)
        self.assertEqual(string_to_encode, decoded_string)

    def test_html_wrap(self):
        cache = html_cache(log_level=logging.ERROR)
        html_string = "<p>Hello, world!</p>"
        wrapped = cache.wrap_html('test', html_string)
        lines = [
            "<span DJERBA_COMPONENT_START='test' />",
            "<p>Hello, world!</p>",
            "<span DJERBA_COMPONENT_END='test' />",
            ""
        ]
        self.assertEqual(wrapped, '\n'.join(lines))

    def test_name_from_separator(self):
        # get component name from the start/finish tag
        good = "<span DJERBA_COMPONENT_START='test'/>"
        broken1 = "<span DJERBA_COMPONENT_START='test'/>blahblah"
        broken2 = "blahblah<span DJERBA_COMPONENT_START='test'/>"
        broken3 = "lorem ipsum dolor"
        broken4 = "<span DJERBA_COMPONENT_NOWHERE='test'/>"
        cache = html_cache(log_level=logging.CRITICAL)
        self.assertEqual(cache.parse_name_from_separator(good), 'test')
        for tag in [broken1, broken2, broken3, broken4]:
            with self.assertRaises(DjerbaHtmlCacheError):
                cache.parse_name_from_separator(tag)

    def test_update_cached(self):
        with open(os.path.join(self.test_source_dir, 'example.html')) as in_file:
            old_html_string = in_file.read()
        tmp_log = os.path.join(self.tmp_dir, 'djerba.log')
        cache = html_cache(log_level=logging.DEBUG, log_path=tmp_log)
        old_html = cache.encode_to_base64(old_html_string)
        new_html = {
            'test': "<span DJERBA_COMPONENT_START='test'/>\n"+\
            'Duis aute irure dolor in reprehenderit in voluptate velit esse '+\
            'cillum dolore eu fugiat nulla pariatur. This is a Djerba test.\n'+\
            "<span DJERBA_COMPONENT_END='test'/>"
        }
        with self.assertLogs('djerba.core.html_cache', level=logging.DEBUG) as log_context:
            updated_html = cache.update_cached_html(new_html, old_html)
        log_messages = [
            'DEBUG:djerba.core.html_cache:Updating test',
            'DEBUG:djerba.core.html_cache:No update found for test_no_update',
            'DEBUG:djerba.core.html_cache:HTML update done'
        ]
        for msg in log_messages:
            self.assertIn(msg, log_context.output)
        self.assertTrue('This is a Djerba test.' in updated_html)
        self.assertFalse('Ut enim ad minim veniam, quis nostrud' in updated_html)
        self.assertTrue('Excepteur sint occaecat cupidatat non proident' in updated_html)
        # test if the updated html can be updated again
        old_html_2 = cache.encode_to_base64(updated_html)
        new_html_2 = {
            'test': "<span DJERBA_COMPONENT_START='test2'/>\n"+\
            'Duis aute irure dolor in reprehenderit in voluptate velit esse '+\
            "cillum dolore eu fugiat nulla pariatur. This is another Djerba test.\n"+\
            "<span DJERBA_COMPONENT_END='test2'/>",
        }
        updated_html_2 = cache.update_cached_html(new_html_2, old_html_2)
        self.assertTrue('This is another Djerba test.' in updated_html_2)
        self.assertFalse('This is a Djerba test.' in updated_html_2)
        self.assertTrue('Excepteur sint occaecat cupidatat non proident' in updated_html)


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
            self.assertEqual(in_file_2.read(), in_file_1.read())

    def test_script(self):
        out_path = os.path.join(self.tmp_dir, 'generated.ini')
        cmd = ['generate_ini.py', '--out', out_path]
        cmd.extend(self.COMPONENT_NAMES)
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        expected_ini_path = os.path.join(self.test_source_dir, 'generated.ini')
        with open(out_path) as in_file_1, open(expected_ini_path) as in_file_2:
            self.assertEqual(in_file_2.read(), in_file_1.read())

class TestLoader(TestCore):
    """Test loading from multiple top-level packages"""

    def test(self):
        var = plugin_loader.DJERBA_PACKAGES
        if var in os.environ:
            original = copy(os.environ[var])
        else:
            original = None
        os.environ[var] = 'alternate_djerba:djerba'
        loader = plugin_loader(log_level=logging.WARNING)
        plugin = loader.load('demo4', workspace(self.tmp_dir))
        self.assertTrue(isinstance(plugin, djerba.plugins.base.plugin_base))
        plugin = loader.load('demo2', workspace(self.tmp_dir))
        self.assertTrue(isinstance(plugin, djerba.plugins.base.plugin_base))
        # remove the alternate package; make a loader with new environment
        os.environ[var] = 'djerba'
        new_loader = plugin_loader(log_level=logging.CRITICAL)
        with self.assertRaises(DjerbaLoadError):
            plugin = new_loader.load('demo4', workspace(self.tmp_dir))
        # reset the environment to its original value
        if original:
            os.environ[var] = original

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
        self.assertEqual(self.SIMPLE_CONFIG_MD5, self.getMD5(out_path))

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
        mode = 'render'
        work_dir = self.tmp_dir
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        cmd = [
            'djerba.py', mode,
            '--json', json_path,
            '--out-dir', self.tmp_dir
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        with open(html_path) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, self.SIMPLE_REPORT_MD5)

    def test_report_cli(self):
        mode = 'report'
        work_dir = self.tmp_dir
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        html = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        cmd = [
            'djerba.py', mode,
            '--work-dir', work_dir,
            '--ini', ini_path,
            '--out-dir', self.tmp_dir
        ]
        result = subprocess_runner().run(cmd)
        pattern = os.path.join(self.tmp_dir, '*'+core_constants.REPORT_JSON_SUFFIX)
        json_path = glob(pattern).pop(0)
        self.assertEqual(result.returncode, 0)
        self.assertSimpleReport(json_path, html)

    def test_setup_cli(self):
        mode = 'setup'
        ini_path = os.path.join(self.tmp_dir, 'config.ini')
        html = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        cmd = [
            'djerba.py', mode,
            '--assay', 'wgts',
            '--ini', ini_path,
            '--compact'
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.getMD5(ini_path), 'e350cdda6a46d4f58647d172067a2d29')
        os.remove(ini_path)
        prepop_path = os.path.join(self.test_source_dir, 'prepop.ini')
        cmd.extend(['--pre-populate', prepop_path])
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.getMD5(ini_path), 'a32e075e861539b68ab510cdb61733fb')

    def test_update_cli_with_ini(self):
        mode = 'update'
        work_dir = self.tmp_dir
        # write an INI file with the correct test directory
        ini_template_path = os.path.join(self.test_source_dir, 'update.ini')
        with open(ini_template_path) as in_file:
            ini_template_string = in_file.read()
        ini_template = Template(ini_template_string)
        ini_string = ini_template.substitute({'TEST_SOURCE_DIR': self.test_source_dir})
        ini_path = os.path.join(self.tmp_dir, 'update.ini')
        with open(ini_path, 'w') as out_file:
            print(ini_string, file=out_file)
        # run djerba.py and check the results
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_UPDATE_JSON)
        cmd = [
            'djerba.py', mode,
            '--work-dir', work_dir,
            '--ini', ini_path,
            '--json', json_path,
            '--out-dir', self.tmp_dir,
            '--pdf'
        ]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        with open(html_path) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, 'c60ea6448d35f6b6d5685d3b095cba03')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        self.assertTrue(os.path.isfile(pdf_path))
        updated_path = os.path.join(self.tmp_dir, 'simple_report_for_update.updated.json')
        self.assertTrue(os.path.isfile(updated_path))

    def test_update_cli_with_summary(self):
        # run with summary-only input
        mode = 'update'
        work_dir = self.tmp_dir
        summary_path = os.path.join(self.test_source_dir, 'alternate_summary.txt')
        # run djerba.py and check the results
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_UPDATE_JSON)
        cmd_base = [
            'djerba.py', mode,
            '--work-dir', work_dir,
            '--summary', summary_path,
            '--out-dir', self.tmp_dir,
            '--pdf'
        ]
        cmd = cmd_base + ['--json', json_path]
        result = subprocess_runner().run(cmd)
        self.assertEqual(result.returncode, 0)
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        with open(html_path) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, '781d477894d5a6e269cb68535a82ca89')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        self.assertTrue(os.path.isfile(pdf_path))
        updated_path = os.path.join(self.tmp_dir, 'simple_report_for_update.updated.json')
        self.assertTrue(os.path.isfile(updated_path))
        # test again with a failed report
        for output in [html_path, pdf_path, updated_path]:
            os.remove(output)
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_UPDATE_FAILED_JSON)
        cmd_failed = cmd_base + ['--json', json_path]
        result = subprocess_runner().run(cmd_failed)
        self.assertEqual(result.returncode, 0)
        html_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        with open(html_path) as html_file:
            html_string = html_file.read()
        self.assert_report_MD5(html_string, '093ca0030bcb2a69d9ac4d784a19b147')
        pdf_path = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        self.assertTrue(os.path.isfile(pdf_path))
        updated_path = os.path.join(self.tmp_dir, 'simple_report_for_update_failed.updated.json')
        self.assertTrue(os.path.isfile(updated_path))


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
        djerba_main = main(self.tmp_dir, log_level=logging.ERROR)
        with self.assertLogs('djerba.core.main', level=logging.DEBUG) as log_context:
            config = djerba_main.configure(ini_path)
        priority_results = [
            ['core', 100, 1],
            ['demo1', 200, 2],
            ['demo2', 300, 3],
            ['gene_information_merger', 2000, 4]
        ]
        prefix = 'DEBUG:djerba.core.main:Configuring'
        template = '{0} {1}, priority {2}, order {3}'
        for (name, priority, order) in priority_results:
            msg = template.format(prefix, name, priority, order)
            self.assertIn(msg, log_context.output)
        # now give demo2 a higher priority than demo1
        config.set('demo1', core_constants.CONFIGURE_PRIORITY, '300')
        config.set('demo2', core_constants.CONFIGURE_PRIORITY, '200')
        ini_path_2 = os.path.join(self.tmp_dir, 'config_modified.ini')
        with open(ini_path_2, 'w') as out_file:
            config.write(out_file)
        with self.assertLogs('djerba.core.main', level=logging.DEBUG) as log_context:
            djerba_main.configure(ini_path_2)
        priority_results = [
            ['core', 100, 1],
            ['demo2', 200, 2], # <---- changed order
            ['demo1', 300, 3],
            ['gene_information_merger', 2000, 4]
        ]
        for (name, priority, order) in priority_results:
            msg = template.format(prefix, name, priority, order)
            self.assertIn(msg, log_context.output)

    def test_extract_priority(self):
        # core and merger do not have extract steps
        ini_path = os.path.join(self.test_source_dir, 'config_full.ini')
        djerba_main = main(self.tmp_dir, log_level=logging.ERROR)
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
        djerba_main = main(self.tmp_dir, log_level=logging.ERROR)
        with open(json_path) as json_file:
            data = json.loads(json_file.read())
        output = djerba_main.render(data)
        html = output['documents']['placeholder_report.clinical']
        pos1 = self.find_line_position(html, 'demo1')
        pos2 = self.find_line_position(html, 'The Question') # demo2 output
        self.assertNotEqual(0, pos1)
        self.assertNotEqual(0, pos2)
        self.assertTrue(pos1 < pos2)
        # now give demo2 a higher priority than demo1
        data['plugins']['demo1']['priorities']['render'] = 200
        data['plugins']['demo2']['priorities']['render'] = 100
        output = djerba_main.render(data)
        html = output['documents']['placeholder_report.clinical']
        pos1 = self.find_line_position(html, 'demo1')
        pos2 = self.find_line_position(html, 'The Question') # demo2 output
        self.assertNotEqual(0, pos1)
        self.assertNotEqual(0, pos2)
        self.assertTrue(pos1 > pos2) # <---- changed order

class TestSimpleReport(TestCore):

    def test_report(self):
        ini_path = os.path.join(self.test_source_dir, 'config.ini')
        json_path = os.path.join(self.test_source_dir, self.SIMPLE_REPORT_JSON)
        djerba_main = main(self.tmp_dir, log_level=logging.ERROR) # suppress author warning
        config = djerba_main.configure(ini_path)
        data_found = djerba_main.extract(config)
        data_found['core']['extract_time'] = '2024-01-01_12:00:00 -0500'
        data_found['core']['core_version'] = 'placeholder'
        data_found['html_cache']['placeholder_report.clinical'] = 'placeholder'
        with open(json_path) as json_file:
            data_expected = json.loads(json_file.read())
        self.assertEqual(data_expected, data_found)
        output = djerba_main.render(data_found, out_dir=self.tmp_dir, pdf=True)
        html_string = output['documents']['placeholder_report.clinical']
        self.assert_report_MD5(html_string, self.SIMPLE_REPORT_MD5)
        # minimal test of HTML/PDF writing; TODO add more PDF tests
        html_out = os.path.join(self.tmp_dir, 'placeholder_report.clinical.html')
        pdf_out = os.path.join(self.tmp_dir, 'placeholder_report.clinical.pdf')
        self.assertTrue(os.path.exists(html_out))
        self.assertTrue(os.path.exists(pdf_out))

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
