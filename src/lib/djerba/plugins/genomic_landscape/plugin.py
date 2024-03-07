"""
Plugin for genomic landscape section.
"""
import csv
import os

import djerba.core.constants as core_constants
import djerba.plugins.genomic_landscape.constants as glc
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

    def specify_params(self):
        discovered = [
            glc.TUMOUR_ID,
            oncokb_constants.ONCOTREE_CODE,
            glc.TCGA_CODE,
            glc.PURITY_INPUT,
            glc.MSI_FILE,
            glc.CTDNA_FILE,
            glc.HRDETECT_PATH
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
        self.set_ini_default('configure_priority', 100)
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
        dsi = core_constants.DEFAULT_SAMPLE_INFO
        dpi = core_constants.DEFAULT_PATH_INFO
        oc = oncokb_constants.ONCOTREE_CODE
        w = self.update_wrapper_if_null(w, ipf, glc.TCGA_CODE)
        w = self.update_wrapper_if_null(w, ipf, glc.PURITY_INPUT)
        w = self.update_wrapper_if_null(w, ipf, oc, self.INPUT_PARAMS_ONCOTREE_CODE)
        w = self.update_wrapper_if_null(w, dsi, glc.TUMOUR_ID)
        w = self.update_wrapper_if_null(w, dpi, glc.MSI_FILE, glc.MSI_WORKFLOW)
        w = self.update_wrapper_if_null(w, dpi, glc.CTDNA_FILE, glc.CTDNA_WORKFLOW)
        w = self.update_wrapper_if_null(w, dpi, glc.HRDETECT_PATH, glc.HRD_WORKFLOW)
        return w.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        tumour_id = wrapper.get_my_string(glc.TUMOUR_ID)
        tcga_code = wrapper.get_my_string(glc.TCGA_CODE).lower()  # always lowercase

        # Get directories
        finder = directory_finder(self.log_level, self.log_path)
        data_dir = finder.get_data_dir()
        work_dir = self.workspace.get_work_dir()
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        r_script_dir = os.path.join(plugin_dir, 'Rscripts')

        # Make a file where all the (actionable) biomarkers will go
        biomarkers_path = self.make_biomarkers_maf(work_dir)
        results = tmb_processor(self.log_level, self.log_path).run(
            work_dir, data_dir, r_script_dir, tcga_code, biomarkers_path, tumour_id
        )
        results[glc.PURITY] = wrapper.get_my_float(glc.PURITY_INPUT) * 100
        results[glc.CTDNA] = ctdna_processor(self.log_level, self.log_path).run(wrapper.get_my_string(glc.CTDNA_FILE))
        hrd = hrd_processor(self.log_level, self.log_path)
        results[glc.BIOMARKERS][glc.HRD] = hrd.run(
            work_dir, wrapper.get_my_string(glc.HRDETECT_PATH)
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
        merge_inputs = self.get_merge_inputs(annotated_maf)
        hrd_annotation = hrd.annotate_NCCN(
            results[glc.BIOMARKERS][glc.HRD]['Genomic biomarker alteration'],
            wrapper.get_my_string(oncokb_constants.ONCOTREE_CODE),
            data_dir
        )
        if hrd_annotation != None:
            merge_inputs.append(hrd_annotation)
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

    def get_merge_inputs(self, annotated_maf_path):
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
                # record therapy for all actionable alterations (OncoKB level 4 or higher)
                therapies = oncokb_levels.parse_actionable_therapies(row_input)
                for level in therapies.keys():
                    gene = 'Biomarker'
                    treatment_entry = treatment_option_factory.get_json(
                        tier=oncokb_levels.tier(level),
                        level=level,
                        gene=gene,
                        alteration=row_input['ALTERATION'],
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
