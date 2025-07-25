"""
Plugin for genomic landscape section.
"""
import csv
import os
import re

import djerba.core.constants as core_constants
import djerba.plugins.sample.constants as sample_constants
import djerba.plugins.genomic_landscape.constants as glc
import djerba.plugins.wgts.cnv_purple.constants as purple_constants
import djerba.util.oncokb.constants as oncokb_constants
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.plugins.base import plugin_base
from djerba.plugins.genomic_landscape.ctdna import ctdna_processor
from djerba.plugins.genomic_landscape.hrd import hrd_processor
from djerba.plugins.genomic_landscape.msi import msi_processor
from djerba.plugins.genomic_landscape.tmb import tmb_processor
from djerba.util.environment import directory_finder
from djerba.util.oncokb.annotator import annotator_factory
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.render_mako import mako_renderer
from djerba.core.workspace import workspace

class main(plugin_base):
    PLUGIN_VERSION = '2.0.0'
    TEMPLATE_NAME = 'genomic_landscape_template.html'

    # TODO standardize this constant, see ticket GCGI-1290
    INPUT_PARAMS_ONCOTREE_CODE = 'oncotree_code'

    # For MSI file
    MSI_RESULTS_SUFFIX = '.recalibrated.msi.booted'
    MSI_WORKFLOW = 'msisensor'

    # For ctDNA file
    CTDNA_RESULTS_SUFFIX = 'SNP.count.txt'
    CTDNA_WORKFLOW = 'mrdetect_filter_only'
    CTDNA_FILE_NOT_FOUND = 'ctDNA file not available'

    # thresholds to evaluate HRD
    MIN_HRD_PURITY = 0.5
    MIN_HRD_PURITY_NOT_FFPE = 0.3
    MAX_HRD_COVERAGE = 115

    def specify_params(self):
        discovered = [
            glc.TUMOUR_ID,
            oncokb_constants.ONCOTREE_CODE,
            glc.TCGA_CODE,
            glc.PURITY_INPUT,
            glc.MSI_FILE,
            glc.CTDNA_FILE,
            glc.HRDETECT_PATH,
            glc.SAMPLE_TYPE
        ]
        for key in discovered:
            self.add_ini_discovered(key)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_ini_default(
            oncokb_constants.ONCOKB_CACHE,
            oncokb_constants.DEFAULT_CACHE_PATH
        )
        self.set_ini_default(oncokb_constants.APPLY_CACHE, False)
        self.set_ini_default(oncokb_constants.UPDATE_CACHE, False)

        # Default parameters for priorities
        self.set_ini_default('configure_priority', 500)
        self.set_ini_default('extract_priority', 1000)
        self.set_ini_default('render_priority', 500)

        # Default parameters for clinical, supplementary
        self.set_ini_default(core_constants.CLINICAL, True)
        self.set_ini_default(core_constants.SUPPLEMENTARY, False)
        self.set_ini_default('attributes', 'clinical')

    def configure(self, config):
        config = self.apply_defaults(config)
        w = self.get_config_wrapper(config)
        ipf = input_params_helper.INPUT_PARAMS_FILE
        ppf = purple_constants.PURITY_PLOIDY
        dsi = core_constants.DEFAULT_SAMPLE_INFO
        dpi = core_constants.DEFAULT_PATH_INFO
        oc = oncokb_constants.ONCOTREE_CODE
        w = self.update_wrapper_if_null(w, ipf, glc.TCGA_CODE)
        w = self.update_wrapper_if_null(w, ipf, glc.SAMPLE_TYPE, fallback=glc.UNKNOWN_SAMPLE_TYPE)
        w = self.update_wrapper_if_null(w, ipf, oc, self.INPUT_PARAMS_ONCOTREE_CODE)
        w = self.update_wrapper_if_null(w, ppf, purple_constants.PURITY)
        w = self.update_wrapper_if_null(w, dsi, glc.TUMOUR_ID)
        w = self.update_wrapper_if_null(w, dpi, glc.MSI_FILE, glc.MSI_WORKFLOW)
        w = self.update_wrapper_if_null(w, dpi, glc.CTDNA_FILE, glc.CTDNA_WORKFLOW)
        w = self.update_wrapper_if_null(w, dpi, glc.HRDETECT_PATH, glc.HRD_WORKFLOW)
        w = self.set_ctdna_file(w, dpi)
        return w.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        tumour_id = wrapper.get_my_string(glc.TUMOUR_ID)
        tcga_code = wrapper.get_my_string(glc.TCGA_CODE).lower()  # always lowercase
        # Get directories
        plugin_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        work_dir = self.workspace.get_work_dir()
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        r_script_dir = os.path.join(plugin_dir, 'Rscripts')
        # Make a file where all the (actionable) biomarkers will go, and initialize results
        biomarkers_path = self.make_biomarkers_maf(work_dir)
        results = tmb_processor(self.log_level, self.log_path).run(
            work_dir, plugin_data_dir, r_script_dir, tcga_code, biomarkers_path, tumour_id
        )
        
        # Get coverage for reporting HRD
        coverage = float(self.workspace.read_maybe_json(sample_constants.QC_SAMPLE_INFO)[sample_constants.COVERAGE_MEAN])

        # evaluate HRD and MSI reportability
        hrd_ok, msi_ok, cant_report_hrd_reason = self.evaluate_reportability(
            wrapper.get_my_float(glc.PURITY_INPUT),
            coverage,
            wrapper.get_my_string(glc.SAMPLE_TYPE)
        )
        results[glc.CAN_REPORT_HRD] = hrd_ok
        results[glc.CAN_REPORT_MSI] = msi_ok
        results[glc.CANT_REPORT_HRD_REASON] = cant_report_hrd_reason

        # evaluate biomarkers
        ctdna_file = wrapper.get_my_string(glc.CTDNA_FILE)
        ctdna_proc = ctdna_processor(self.log_level, self.log_path)
        if ctdna_file == self.CTDNA_FILE_NOT_FOUND:
            results[glc.CTDNA] = ctdna_proc.get_dummy_results()
        else:
            results[glc.CTDNA] = ctdna_proc.run(ctdna_file)
        hrd = hrd_processor(self.log_level, self.log_path)
        results[glc.BIOMARKERS][glc.HRD] = hrd.run(
            work_dir,
            wrapper.get_my_string(glc.HRDETECT_PATH)
        )
        results[glc.BIOMARKERS][glc.MSI] = msi_processor(self.log_level, self.log_path).run(
            work_dir,
            r_script_dir,
            wrapper.get_my_string(glc.MSI_FILE),
            biomarkers_path,
            tumour_id
        )
        # Annotate genomic biomarkers for therapy info/merge inputs
        annotated_maf = self.annotate_oncokb(work_dir, wrapper)
        merge_inputs = self.get_oncokb_merge_inputs(annotated_maf, msi_ok)
        hrd_annotation = hrd.annotate_NCCN(
            results[glc.BIOMARKERS][glc.HRD]['Genomic biomarker alteration'],
            wrapper.get_my_string(oncokb_constants.ONCOTREE_CODE),
            plugin_data_dir,
            directory_finder(self.log_level, self.log_path).get_data_dir()
        )
        if hrd_annotation:
            if hrd_ok:
                merge_inputs.append(hrd_annotation)
            else:
                self.logger.debug('Omitting HRD annotation from therapies')
        else:
            self.logger.debug('No actionable annotation for HRD')
        data['merge_inputs']['treatment_options_merger'] = merge_inputs
        data['results'] = results
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)

    def annotate_oncokb(self, work_dir, wrapper):
        """
        Annotate for treatment options -- includes OncoKB caching
        """
        input_path = os.path.join(work_dir, glc.GENOMIC_BIOMARKERS)
        output_path = os.path.join(work_dir, glc.GENOMIC_BIOMARKERS_ANNOTATED)
        factory = annotator_factory(self.log_level, self.log_path)
        annotator = factory.get_annotator(work_dir, wrapper)
        annotator.annotate_biomarkers_maf(input_path, output_path)
        return output_path

    def evaluate_reportability(self, purity, coverage, sample_type):
        # evaluate reportability for HRD and MSI metrics
        self.logger.debug('Evaluating reportability for purity and sample type')
        sample_is_ffpe = False
        if re.search('FFPE', sample_type.upper()):
            sample_is_ffpe = True
            self.logger.debug('FFPE sample detected')
        elif sample_type == glc.UNKNOWN_SAMPLE_TYPE:
            self.logger.warning("Unknown sample type in config; assuming non-FFPE sample")
        else:
            self.logger.debug('Non-FFPE sample detected')
        hrd_purity_ok = purity>=self.MIN_HRD_PURITY or (purity>=self.MIN_HRD_PURITY_NOT_FFPE and not sample_is_ffpe)
        if hrd_purity_ok and coverage <= self.MAX_HRD_COVERAGE:
            hrd_ok = True
            cant_report_hrd_reason = False
        elif coverage > self.MAX_HRD_COVERAGE:
            hrd_ok = False
            cant_report_hrd_reason = glc.COVERAGE_REASON
        else:
            hrd_ok = False
            cant_report_hrd_reason = glc.PURITY_REASON
        if purity >= 0.5:
            msi_ok = True
        else:
            msi_ok = False
        self.logger.debug("HRD reportable: {0}".format(hrd_ok))
        self.logger.debug("MSI reportable: {0}".format(msi_ok))
        return (hrd_ok, msi_ok, cant_report_hrd_reason)

    def get_oncokb_merge_inputs(self, annotated_maf_path, msi_ok):
        """
        Read therapy information for merge inputs
        This is derived from the annotated biomarkers file.
        This does not build gene information
        (i.e. MSI and TMB are not included in the gene glossary).
        """
        # read the tab-delimited input file
        treatments = []
        treatment_option_factory = tom_factory(self.log_level, self.log_path)
        with open(annotated_maf_path) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row_input in reader:
                alteration = row_input['ALTERATION']
                if re.search('MSI', alteration.upper()) and not msi_ok:
                    self.logger.debug('Omitting MSI from therapies: {0}'.format(alteration))
                    continue
                # record therapy for all actionable alterations (OncoKB level 4 or higher)
                therapies = oncokb_levels.parse_actionable_therapies(row_input)
                for level in therapies.keys():
                    gene = 'Biomarker'
                    treatment_entry = treatment_option_factory.get_json(
                        tier=oncokb_levels.tier(level),
                        level=level,
                        gene=gene,
                        alteration=alteration,
                        alteration_url=self.get_alt_url(row_input['ALTERATION']),
                        treatments=therapies[level]
                    )
                    treatments.append(treatment_entry)
        # assemble the output
        return treatments

    def make_biomarkers_maf(self, work_dir):
        maf_header = '\t'.join(["HUGO_SYMBOL", "SAMPLE_ID", "ALTERATION"])
        genomic_biomarkers_path = os.path.join(work_dir, glc.GENOMIC_BIOMARKERS)
        with open(genomic_biomarkers_path, 'w') as genomic_biomarkers_file:
            # Write the header into the file 
            print(maf_header, file=genomic_biomarkers_file)
        return genomic_biomarkers_path

    def get_alt_url(self, alteration):
        core_biomarker_url = "https://www.oncokb.org/gene/Other%20Biomarkers"
        if alteration == "TMB-H":
            alt_url = '/'.join([core_biomarker_url, "TMB-H/"])
        elif alteration == "MSI-H":
            alt_url = '/'.join([core_biomarker_url, "Microsatellite%20Instability-High/"])
        else:
            msg = "Unknown alteration '{0}', cannot generate URL".format(alteration)
            self.logger.error(msg)
            raise RuntimeError(msg)
        return alt_url

    def set_ctdna_file(self, cw, info_name):
        # ctDNA file is required for clinical reports, optional otherwise
        # cw is a config_wrapper object; info name is name of the path info JSON file
        cw = self.update_wrapper_if_null(cw, info_name, glc.CTDNA_FILE, glc.CTDNA_WORKFLOW)
        ctdna_file = cw.get_my_string(glc.CTDNA_FILE)
        if ctdna_file == 'None':
            self.logger.debug('ctDNA file not found in provenance or manual inputs')
            if core_constants.CLINICAL in cw.get_my_attributes():
                msg = "Clinical report cannot proceed without mrdetect ctDNA file"
                self.logger.error(msg)
                raise RuntimeError(msg)
            else:
                cw.set_my_param(glc.CTDNA_FILE, self.CTDNA_FILE_NOT_FOUND)
                self.logger.debug('Non-clinical research report, ctDNA file is not required')
        else:
            self.logger.debug("Found ctDNA file: '{0}'".format(ctdna_file))
        return cw
