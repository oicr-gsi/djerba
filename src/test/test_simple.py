#! /usr/bin/env python3

import configparser
import hashlib
import json
import jsonschema
import os
import subprocess
import tempfile
import unittest
import djerba.simple.constants as constants
import djerba.simple.ini_fields as ini
from jsonschema.exceptions import ValidationError
from djerba.simple.configure.configure import config_updater, provenance_reader, MissingProvenanceError
from djerba.simple.extract.extractor import extractor
from djerba.simple.extract.r_script_wrapper import r_script_wrapper
from djerba.simple.extract.sequenza import sequenza_extractor, SequenzaExtractionError
from djerba.simple.build.reader import json_reader, mastersheet_reader, multiple_reader
from djerba.simple.runner import runner

class TestBase(unittest.TestCase):

    def getMD5(self, inputPath):
        md5 = hashlib.md5()
        with open(inputPath, 'rb') as f:
            md5.update(f.read())
        return md5.hexdigest()

    def run_command(self, cmd):
        """Run a command; in case of failure, capture STDERR."""
        result = subprocess.run(cmd, encoding=constants.TEXT_ENCODING, capture_output=True)
        try:
            result.check_returncode()
        except subprocess.CalledProcessError as err:
            msg = "Script failed with STDERR: "+result.stderr
            raise RuntimeError(msg) from err
        return result

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        # specify all non-public data paths relative to self.sup_dir
        # modified test provenance file gets its own environment variable
        sup_dir_var = 'DJERBA_TEST_DATA'
        provenance_var = 'DJERBA_TEST_PROVENANCE'
        self.sup_dir = os.environ.get(sup_dir_var)
        self.provenance_path = os.environ.get(provenance_var)
        if not (self.sup_dir):
            raise RuntimeError('Need to specify environment variable {0}'.format(sup_dir_var))
        elif not os.path.isdir(self.sup_dir):
            raise OSError("Supplementary directory path '{0}' is not a directory".format(self.sup_dir))
        if not self.provenance_path:
            raise RuntimeError('Need to specify environment variable {0}'.format(provenance_var))
        elif not os.path.isfile(self.provenance_path):
            raise OSError("Provenance path '{0}' is not a file".format(self.provenance_path))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_simple_')
        self.tmpDir = self.tmp.name
        self.schema_path = os.path.join(self.sup_dir, 'elba_config_schema.json')
        self.bed_path = os.path.join(self.sup_dir, 'S31285117_Regions.bed')
        self.dummy_maf_name = 'PANX_1249_Lv_M_WG_100-PM-013_LCM5.filter.deduped.realigned.recalibrated.mutect2.tumor_only.filtered.unmatched.DUMMY.maf.gz'
        self.dummy_maf_path = os.path.join(self.sup_dir, self.dummy_maf_name)
        self.project = 'PASS01'
        self.donor = 'PANX_1249'
        with open(self.schema_path) as f:
            self.schema = json.loads(f.read())
        self.rScriptDir = os.path.realpath(os.path.join(self.testDir, '../lib/djerba/simple/R/'))

    def tearDown(self):
        self.tmp.cleanup()

class TestConfigure(TestBase):

    def test_reader(self):
        test_reader = provenance_reader(self.provenance_path, self.project, self.donor)
        maf_path = test_reader.parse_maf_path()
        expected = self.dummy_maf_path
        self.assertEqual(maf_path, expected)
        with self.assertRaises(MissingProvenanceError):
            test_reader_2 = provenance_reader(self.provenance_path, self.project, 'nonexistent_donor')

    def test_updater(self):
        iniPath = os.path.join(self.dataDir, 'config.ini')
        config = configparser.ConfigParser()
        config.read(iniPath)
        updater = config_updater(config)
        updater.update()
        #updated_path = os.path.join(self.tmpDir, 'updated_config.ini')
        updated_path = os.path.join('/home/iain/tmp', 'updated_config.ini')
        with open(updated_path, 'w') as f:
            updater.get_config().write(f)
        # TODO this relies on local paths being identical; make it portable
        self.assertEqual(self.getMD5(updated_path), '72a8676a348a82e7d0dcbc896eb88972')

class TestExtractor(TestBase):

    def setUp(self):
        super().setUp()
        self.iniPath = os.path.join(self.sup_dir, 'rscript_config_updated.ini')

    def test_writeIniParams(self):
        outDir = '/home/iain/tmp/djerba/test/extractor' # TODO change to testing temp dir
        config = configparser.ConfigParser()
        config.read(self.iniPath)
        config[ini.SETTINGS][ini.SCRATCH_DIR] = outDir
        ex = extractor(config)
        ex.run()
        self.assertEqual(
            self.getMD5(os.path.join(outDir, 'maf_params.json')),
            '1bfd7eb6d0bb974b02f6e13e63074001'
        )
        self.assertEqual(
            self.getMD5(os.path.join(outDir, 'sequenza_params.json')),
            '48ad764f0da71feeda301cd2c71d1627'
        )


class TestReader(TestBase):

    def setUp(self):
        super().setUp()
        self.components = []
        component_filenames = ['json_reader_component_%d.json' % i for i in range(1,4)]
        for name in component_filenames:
            with open(os.path.join(self.dataDir, name)) as f:
                self.components.append(json.loads(f.read()))

    def test_mastersheet_reader(self):
        ms_component_path = os.path.join(self.dataDir, 'mastersheet_reader_component.json')
        with open(ms_component_path) as f:
            ms_component = json.loads(f.read())
        ms_component['mastersheet_path'] = os.path.join(self.dataDir, 'mastersheet-v1.psv')
        reader = mastersheet_reader(ms_component, self.schema)
        patient_id = reader.get_sample_info().get_attribute('PATIENT_ID')
        self.assertEqual(patient_id, '123-456-789')

    def test_json_reader(self):
        # read a component path with all fields specified
        reader1 = json_reader(self.components[0], self.schema)
        self.assertEqual(reader1.total_genes(), 2)
        for gene in reader1.get_genes_list():
            self.assertEqual(len(gene.get_attributes()), 17)
        self.assertEqual(len(reader1.get_sample_info().get_attributes()), 34)
        self.assertTrue(reader1.is_complete())
        self.assertIsNone(jsonschema.validate(reader1.get_output(), self.schema))
        # insert a value not permitted by the schema; output validation now fails
        reader1.sample_info.attributes['ORDERING_PHYSICIAN'] = 999
        with self.assertRaises(ValidationError):
            reader1.get_output()
        # read an incomplete component path
        reader2 = json_reader(self.components[1], self.schema)
        self.assertEqual(reader2.total_genes(), 2)
        for gene in reader2.get_genes_list():
            self.assertEqual(len(gene.get_attributes()), 9)
        self.assertEqual(len(reader2.get_sample_info().get_attributes()), 14)
        self.assertFalse(reader2.is_complete())
        with self.assertRaises(RuntimeError):
            reader2.get_output()

    def test_multiple_reader(self):
        # multiple reader with consistent values
        reader1 = multiple_reader(self.components[0:2], self.schema)
        self.assertEqual(reader1.total_genes(), 2)
        for gene in reader1.get_genes_list():
            self.assertEqual(len(gene.get_attributes()), 17)
        self.assertEqual(len(reader1.get_sample_info().get_attributes()), 34)
        self.assertTrue(reader1.is_complete())
        self.assertIsNone(jsonschema.validate(reader1.get_output(), self.schema))
        # inconsistent values
        with self.assertRaises(ValueError):
            reader2 = multiple_reader([self.components[0], self.components[2]], self.schema)

class TestRunner(TestBase):

    def setUp(self):
        super().setUp()
        # TODO output has sample name = null; will change once carried-through params are updated
        self.expectedMD5 = 'ca2850a3acda9f47bcc01fe04ee359a9'
        self.iniPath = os.path.join(self.dataDir, 'config.ini')
        self.workDir = os.path.join(self.tmpDir, 'work')
        os.mkdir(self.workDir)
        
    def test_runner(self):
        #outPath = os.path.join(self.tmpDir, 'report.json')
        # TODO customize INI params to use temporary test dir
        outDir = '/home/iain/oicr/workspace/djerba/cli_output_wip'
        outPath = os.path.join(outDir, 'cgi_metrics.json')
        config = configparser.ConfigParser()
        config.read(self.iniPath)
        runner(config).run()
        self.assertEqual(self.getMD5(outPath), self.expectedMD5)

    def test_script(self):
        outDir = '/home/iain/oicr/workspace/djerba/cli_output_wip'  # TODO replace with tempdir
        outPath = os.path.join(outDir, 'cgi_metrics.json')
        cmd = [
            "djerba_simple.py",
            "--ini", self.iniPath
        ]
        self.run_command(cmd)
        self.assertEqual(self.getMD5(outPath), self.expectedMD5)

class TestSequenzaExtractor(TestBase):

    def setUp(self):
        super().setUp()
        self.zip_path = os.path.join(self.sup_dir, 'sequenza', 'PANX_1249_Lv_M_WG_100-PM-013_LCM5_results.zip')
        self.expected_gamma = 400
    
    def test_finder_script(self):
        """Test the command-line script to find gamma"""
        cmd = [
            "sequenza_gamma_selector.py",
            "--in", self.zip_path,
            "--verbose"
        ]
        result = self.run_command(cmd)
        with open(os.path.join(self.dataDir, 'gamma_test.tsv'), 'rt') as in_file:
            expected_params = in_file.read()
        self.assertEqual(int(result.stdout), self.expected_gamma)
        self.assertEqual(result.stderr, expected_params)

    def test_purity_ploidy(self):
        seqex = sequenza_extractor(self.zip_path)
        [purity, ploidy] = seqex.get_purity_ploidy()
        self.assertEqual(purity, 0.6)
        self.assertEqual(ploidy, 3.1)
        expected_segments = {
            50: 8669,
            100: 4356,
            200: 1955,
            300: 1170,
            400: 839,
            500: 622,
            600: 471,
            700: 407,
            800: 337,
            900: 284,
            1000: 245,
            1250: 165,
            1500: 123,
            2000: 84
        }
        self.assertEqual(seqex.get_segment_counts(), expected_segments)
        self.assertEqual(seqex.get_default_gamma(), self.expected_gamma)
        # test with alternate gamma
        [purity, ploidy] = seqex.get_purity_ploidy(gamma=50)
        self.assertEqual(purity, 0.56)
        self.assertEqual(ploidy, 3.2)
        # test with nonexistent gamma
        with self.assertRaises(SequenzaExtractionError):
            seqex.get_purity_ploidy(gamma=999999)

    def test_seg_file(self):
        seqex = sequenza_extractor(self.zip_path)
        seg_path = seqex.extract_seg_file(self.tmpDir)
        self.assertEqual(
            seg_path,
            os.path.join(self.tmpDir, 'gammas/400/PANX_1249_Lv_M_WG_100-PM-013_LCM5_Total_CN.seg')
        )
        self.assertEqual(self.getMD5(seg_path), '25b0e3c01fe77a28b24cff46081cfb1b')
        seg_path = seqex.extract_seg_file(self.tmpDir, gamma=1000)
        self.assertEqual(
            seg_path,
            os.path.join(self.tmpDir, 'gammas/1000/PANX_1249_Lv_M_WG_100-PM-013_LCM5_Total_CN.seg')
        )
        self.assertEqual(self.getMD5(seg_path), '5d433e47431029219b6922fba63a8fcf')
        with self.assertRaises(SequenzaExtractionError):
            seqex.extract_seg_file(self.tmpDir, gamma=999999)

class TestWrapper(TestBase):

    def test(self):
        iniPath = os.path.join(self.sup_dir, 'rscript_config_updated.ini')
        config = configparser.ConfigParser()
        config.read(iniPath)
        test_wrapper = r_script_wrapper(config)
        result = test_wrapper.run()
        self.assertEqual(0, result.returncode)

if __name__ == '__main__':
    unittest.main()
