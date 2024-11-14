"""Do OncoKB annotation by calling the scripts in oncokb-annotator"""

# The Python scripts in oncokb-annotator do not have a class structure and would be difficult to import
# Instead, we run them as subprocesses

import os
import logging
import djerba.core.constants as core_constants
import djerba.util.oncokb.constants as oncokb_constants
import djerba.util.constants as constants
from djerba.util.oncokb.cache import oncokb_cache, oncokb_cache_params
from djerba.util.logger import logger
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.validator import path_validator

class annotator_factory(logger):
    """Create an OncoKB annotator from params in a Djerba config wrapper"""

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def get_annotator(self, work_dir, config_wrapper):
        cache_params = oncokb_cache_params(
            config_wrapper.get_my_string(oncokb_constants.ONCOKB_CACHE),
            config_wrapper.get_my_boolean(oncokb_constants.APPLY_CACHE),
            config_wrapper.get_my_boolean(oncokb_constants.UPDATE_CACHE),
            log_level=self.log_level,
            log_path=self.log_path
        )
        self.logger.debug("OncoKB cache params: {0}".format(cache_params))
        annotator = oncokb_annotator(
            config_wrapper.get_my_string(core_constants.TUMOUR_ID),
            config_wrapper.get_my_string(oncokb_constants.ONCOTREE_CODE),
            work_dir, # output dir
            work_dir, # temporary dir -- same as output
            cache_params,
            self.log_level,
            self.log_path
        )
        return annotator


class oncokb_annotator(logger):

    # environment variable for ONCOKB token path
    ONCOKB_TOKEN_VARIABLE = 'ONCOKB_TOKEN'

    # fields for empty oncoKB annotated fusion file
    ONCOKB_FUSION_ANNOTATED_HEADERS = [
        'Tumor_Sample_Barcode', 'Fusion', 'mutation_effect', 'ONCOGENIC',
        'LEVEL_1', 'LEVEL_2', 'LEVEL_3A', 'LEVEL_3B', 'LEVEL_4',
        'LEVEL_R1', 'LEVEL_R2', 'LEVEL_R3', 'HIGHEST_LEVEL', 'HIGHEST_SENSITIVE_LEVEL',
        'HIGHEST_RESISTANCE_LEVEL'
    ]

    def __init__(self, tumour_id, oncotree_code, report_dir, scratch_dir=None,
                 cache_params=None, log_level=logging.WARNING, log_path=None):
        # report_dir is for input and (persistent) output; must contain appropriate input files
        # if given, scratch_dir is for working files not needed for final output
        # cache_params is a djerba.extract.oncokb.cache.params object
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.validator = path_validator(log_level, log_path)
        self.report_dir = report_dir
        self.validator.validate_output_dir(self.report_dir)
        if scratch_dir:
            self.scratch_dir = scratch_dir
            self.validator.validate_output_dir(self.scratch_dir)
        else:
            self.scratch_dir = self.report_dir
        self.runner = subprocess_runner(log_level, log_path)
        # Write sample name and oncotree code to a file, for use by annotation scripts
        self.info_path = os.path.join(self.scratch_dir, oncokb_constants.ONCOKB_CLINICAL_INFO)
        args = [tumour_id, oncotree_code]
        with open(self.info_path, 'w') as info_file:
            print("SAMPLE_ID\tONCOTREE_CODE", file=info_file)
            print("{0}\t{1}".format(*args), file=info_file)
        # Check cache params and configure caching (if any)
        if cache_params==None:
            self.logger.debug("No OncoKB cache parameters supplied; cache operations omitted")
            cache_params = oncokb_cache_params() # default values
        else:
            self.logger.debug("Using supplied OncoKB cache parameters: {}".format(cache_params))
        self.apply_cache = cache_params.get_apply_cache()
        self.update_cache = cache_params.get_update_cache()
        # Read the oncokb access token, if needed
        if self.apply_cache:
            self.logger.debug('Apply-cache enabled, no OncoKB access token required')
            self.oncokb_token = None
        else:
            with open(os.environ[self.ONCOKB_TOKEN_VARIABLE]) as token_file:
                self.oncokb_token = token_file.read().strip()
        # Set up the cache, if needed
        if self.apply_cache or self.update_cache:
            cache_dir = cache_params.get_cache_dir()
            self.cache = oncokb_cache(cache_dir, oncotree_code, log_level, log_path)
        else:
            self.cache = None

    def _run_annotator_script(self, command, description):
        """Redact the OncoKB token (-b argument) from logging"""
        self.runner.run(command, description, ['-b',])
        
    def annotate_cna(self, in_file_extension=''):
        in_path = os.path.join(self.report_dir, ''.join((in_file_extension,oncokb_constants.DATA_CNA_ONCOKB_GENES_NON_DIPLOID)))
        self.validator.validate_input_file(in_path)
        out_path = os.path.join(self.report_dir, ''.join((in_file_extension,oncokb_constants.DATA_CNA_ONCOKB_GENES_NON_DIPLOID_ANNOTATED)))
        if self.apply_cache:
            self.cache.annotate_cna(in_path, out_path, self.info_path)
        else:
            cmd = [
                'CnaAnnotator.py',
                '-i', in_path,
                '-o', out_path,
                '-c', self.info_path,
                '-b', self.oncokb_token
            ]
            self._run_annotator_script(cmd, 'CNA annotator')
            if self.update_cache:
                self.cache.write_cna_cache(out_path)
        return out_path

    def annotate_fusion(self):
        in_path = os.path.join(self.report_dir, constants.DATA_FUSIONS_ONCOKB)
        self.validator.validate_input_file(in_path)
        out_path = os.path.join(self.report_dir, oncokb_constants.DATA_FUSIONS_ONCOKB_ANNOTATED)
        with open(in_path) as in_file:
            total = len(in_file.readlines())
        if self.apply_cache:
            self.cache.annotate_fusion(in_path, out_path)
        elif total == 0:
            # should never happen, but include for completeness
            msg = "Fusion input {0} cannot be empty -- header is expected".format(in_path)
            self.logger.error(msg)
            raise RuntimeError(msg)
        elif total==1:
            # input has only a header -- write the oncoKB annotated header
            self.logger.info("Empty fusion input, writing empty oncoKB annotated file")
            with open(out_path, 'w') as out_file:
                out_file.write("\t".join(self.ONCOKB_FUSION_ANNOTATED_HEADERS)+"\n")
        else:
            msg = "Read {0} lines of fusion input, running Fusion annotator".format(total)
            self.logger.debug(msg)
            cmd = ['which', 'FusionAnnotator.py']
            self.runner.run(cmd)
            cmd = [
                'FusionAnnotator.py',
                '-i', in_path,
                '-o', out_path,
                '-c', self.info_path,
                '-b', self.oncokb_token
            ]
            self._run_annotator_script(cmd, 'fusion annotator')
            if self.update_cache:
                self.cache.write_fusion_cache(out_path)
        return out_path

    def annotate_maf(self, in_path):
        # unlike the CNA and Fusion methods, MAF annotation takes an input path argument
        self.validator.validate_input_file(in_path)
        out_path = os.path.join(self.scratch_dir, oncokb_constants.ANNOTATED_MAF)
        if self.apply_cache:
            self.cache.annotate_maf(in_path, out_path)
        else:
            cmd = [
                'MafAnnotator.py',
                '-i', in_path,
                '-o', out_path,
                '-c', self.info_path,
                '-q', 'Genomic_Change',
                '-b', self.oncokb_token
            ]
            self._run_annotator_script(cmd, 'MAF annotator')
            if self.update_cache:
                self.cache.write_maf_cache(out_path)
        return out_path
    
    def annotate_biomarkers_maf(self, in_path, out_path):
        """although it uses the same MafAnnotator script, 
        other biomarkers needs to be seperate because 
        it can't use 'Genomic_Change'"""
        self.validator.validate_input_file(in_path)
        if self.apply_cache:
            self.logger.debug("Applying cache for biomarker annotation")
            self.cache.annotate_maf(in_path, out_path)
        else:
            cmd = [
                'MafAnnotator.py',
                '-i', in_path,
                '-o', out_path,
                '-c', self.info_path,
                '-b', self.oncokb_token
            ]
            self._run_annotator_script(cmd, 'MAF annotator')
            if self.update_cache:
                self.logger.debug("Updating cache for biomarker annotation")
                self.cache.write_maf_cache(out_path)
        return out_path

