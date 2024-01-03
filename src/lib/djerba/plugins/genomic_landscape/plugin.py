"""
Plugin for genomic landscape section.
"""
import os
import csv
from djerba.plugins.base import plugin_base, DjerbaPluginError
from mako.lookup import TemplateLookup
import djerba.core.constants as core_constants
from djerba.plugins.genomic_landscape.provenance_tools import parse_file_path
from djerba.plugins.genomic_landscape.provenance_tools import subset_provenance
from djerba.util.render_mako import mako_renderer
import djerba.util.input_params_tools as input_params_tools
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.oncokb.annotator import oncokb_annotator
from djerba.util.oncokb.tools import levels as oncokb_levels
import djerba.util.oncokb.constants as okb
import djerba.plugins.genomic_landscape.constants as constants
import djerba.plugins.genomic_landscape.msi_functions as msi
import djerba.plugins.genomic_landscape.tmb_functions as tmb
import djerba.plugins.genomic_landscape.ctdna_functions as ctdna
import djerba.plugins.genomic_landscape.hrd_functions as hrd
from djerba.util.html import html_builder as hb
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.helpers.input_params_helper.helper import main as input_params_helper
from djerba.util.environment import directory_finder

class main(plugin_base):
    
    PLUGIN_VERSION = '2.0.0'
    TEMPLATE_NAME = 'genomic_landscape_template.html'

    def build_genomic_biomarkers(self, work_dir, oncotree_code, tumour_ID):
        """
        # Writes and annotates the biomarkers file in the report directory
        """
        self.logger.debug("Annotating Genomic Biomarkers")
        
        # Get input file (to be annotated)
        genomic_biomarkers_path = os.path.join(work_dir, constants.GENOMIC_BIOMARKERS)
        # Get output file (after annotation)
        genomic_biomarkers_annotated = os.path.join(work_dir, constants.GENOMIC_BIOMARKERS_ANNOTATED)
        # Annotate the input file to the output file 
        oncokb_annotator(
            tumour_ID,
            oncotree_code.upper(),
            work_dir,
            cache_params = None,
            log_level=self.log_level,
            log_path=self.log_path
        ).annotate_biomarkers_maf(genomic_biomarkers_path, genomic_biomarkers_annotated)
        # Return data for the biomarkers section of the output JSON

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)

        parameters_to_fill = [
            constants.ONCOTREE_CODE,
            constants.TCGA_CODE
        ]
        for param in parameters_to_fill:
            wrapper = self.fill_param_if_null(wrapper, param, input_params_helper.INPUT_PARAMS_FILE )
 
        wrapper = self.fill_param_if_null(wrapper, constants.PURITY_INPUT, "purity_ploidy.json")
        wrapper = self.fill_param_if_null(wrapper, constants.TUMOUR_ID, core_constants.DEFAULT_SAMPLE_INFO )
        wrapper = self.fill_file_if_null(wrapper, constants.MSI_WORKFLOW, constants.MSI_FILE, core_constants.DEFAULT_PATH_INFO)
        wrapper = self.fill_file_if_null(wrapper, constants.CTDNA_WORKFLOW, constants.CTDNA_FILE, core_constants.DEFAULT_PATH_INFO)
        wrapper = self.fill_file_if_null(wrapper, constants.HRD_WORKFLOW, constants.HRDETECT_PATH, core_constants.DEFAULT_PATH_INFO)

        return wrapper.get_config()

    def extract(self, config):
        
        wrapper = self.get_config_wrapper(config)
        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
        tumour_id = wrapper.get_my_string(constants.TUMOUR_ID)  

        # Get directories
        finder = directory_finder(self.log_level, self.log_path)
        work_dir = self.workspace.get_work_dir()
        r_script_dir = finder.get_base_dir() + "/plugins/genomic_landscape/Rscripts"

        # Make a file where all the (actionable) biomarkers will go
        biomarkers_path = self.make_biomarkers_maf(work_dir)

        # Get genomic landscape info
        # TMB goes first because it does both a survey and is a biomarker
        results = tmb.run(self, work_dir, finder.get_data_dir(), r_script_dir,  wrapper.get_my_string(constants.TCGA_CODE).lower(), biomarkers_path, tumour_id)
        results[constants.PURITY] = float(wrapper.get_my_string(constants.PURITY_INPUT))*100
        results[constants.CTDNA] = ctdna.run(self, work_dir, wrapper.get_my_string(constants.CTDNA_FILE))
        results[constants.BIOMARKERS][constants.HRD] = hrd.run(work_dir, wrapper.get_my_string(constants.HRDETECT_PATH))
        results[constants.BIOMARKERS][constants.MSI] = msi.run(self, work_dir, r_script_dir, wrapper.get_my_string(constants.MSI_FILE), biomarkers_path, tumour_id)

        # Annotate genomic biomarkers for therapy info/merge inputs
        self.build_genomic_biomarkers(work_dir, wrapper.get_my_string(constants.ONCOTREE_CODE), tumour_id)
        
        merge_inputs = self.get_merge_inputs(work_dir)
        hrd_annotation = hrd.annotate_hrd(results[constants.BIOMARKERS][constants.HRD]['Genomic biomarker alteration'], wrapper.get_my_string(constants.ONCOTREE_CODE), finder.get_data_dir())
        if hrd_annotation != None:
            merge_inputs.append(hrd_annotation)
        data['merge_inputs']['treatment_options_merger'] = merge_inputs
        data['results'] = results

        return data

    def fill_file_if_null(self, wrapper, workflow_name, ini_param, path_info):
        if wrapper.my_param_is_null(ini_param):
            if self.workspace.has_file(path_info):
                path_info = self.workspace.read_json(path_info)
                workflow_path = path_info.get(workflow_name)
                if workflow_path == None:
                    msg = 'Cannot find {0}'.format(ini_param)
                    self.logger.error(msg)
                    raise RuntimeError(msg)
                wrapper.set_my_param(ini_param, workflow_path)
        return(wrapper)

    def fill_param_if_null(self, wrapper, param, input_param_file):
        if wrapper.my_param_is_null(param):
            if self.workspace.has_file(input_param_file):
                data = self.workspace.read_json(input_param_file)
                param_value = data[param]
                wrapper.set_my_param(param, param_value)
            else:
                msg = "Cannot find {0}; must be manually specified or ".format(param)+\
                        "given in {0}".format(input_param_file)
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        return(wrapper)

    def get_alt_url(self, alteration):
        core_biomarker_url = "https://www.oncokb.org/gene/Other%20Biomarkers"
        if alteration == "TMB-H" or alteration == "MSI-H":
            if alteration == "TMB-H":
                alt_url = '/'.join([core_biomarker_url,"TMB-H/"])
            if alteration == "MSI-H":
                alt_url = '/'.join([core_biomarker_url,"Microsatellite%20Instability-High/"])
        return alt_url

    def get_merge_inputs(self, work_dir):
        """
        Read therapy information for merge inputs
        This is derived from the annotated biomarkers file.
        This does not build gene information (i.e. MSI and TMB are not included in the gene glossary).
        """
        # read the tab-delimited input file
        treatments = []
        treatment_option_factory = tom_factory(self.log_level, self.log_path)
        input_name = constants.GENOMIC_BIOMARKERS_ANNOTATED
        with open(os.path.join(work_dir, input_name)) as input_file:
            reader = csv.DictReader(input_file, delimiter="\t")
            for row_input in reader:
                # record therapy for all actionable alterations (OncoKB level 4 or higher)
                therapies = oncokb_levels.parse_actionable_therapies(row_input)
                for level in therapies.keys():
                    gene = 'Biomarker'
                    treatment_entry = treatment_option_factory.get_json(
                        tier = oncokb_levels.tier(level),
                        level = level,
                        gene = gene,
                        alteration = row_input['ALTERATION'],
                        alteration_url = self.get_alt_url(row_input['ALTERATION']),
                        treatments = therapies[level]
                    )
                    treatments.append(treatment_entry)
        # assemble the output
        return treatments

    def make_biomarkers_maf(self, work_dir):
        maf_header = '\t'.join(["HUGO_SYMBOL","SAMPLE_ID","ALTERATION"])
        genomic_biomarkers_path = os.path.join(work_dir, constants.GENOMIC_BIOMARKERS)
        with open(genomic_biomarkers_path, 'w') as genomic_biomarkers_file:
            # Write the header into the file 
            print(maf_header, file=genomic_biomarkers_file)
        return(genomic_biomarkers_path)

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)

    def specify_params(self):
      discovered = [
           constants.TUMOUR_ID,
           constants.ONCOTREE_CODE,
           constants.TCGA_CODE,
           constants.PURITY_INPUT,
           constants.MSI_FILE,
           constants.CTDNA_FILE,
           constants.HRDETECT_PATH
      ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
      self.set_ini_default('configure_priority', 100)
      self.set_ini_default('extract_priority', 1000)
      self.set_ini_default('render_priority', 500)
