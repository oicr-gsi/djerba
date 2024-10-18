"""
Plugin for TAR SWGS.
"""

# IMPORTS
import os
import csv
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.tar.swgs.constants as constants
from djerba.plugins.tar.swgs.preprocess import preprocess
from djerba.plugins.tar.swgs.extract import data_builder 
import djerba.core.constants as core_constants
import gsiqcetl.column
from gsiqcetl import QCETLCache
from djerba.util.render_mako import mako_renderer
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.oncokb.tools import gene_summary_reader

class main(plugin_base):
    
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'html/swgs_template.html'
    CNA_ANNOTATED = "data_CNA_oncoKBgenes_nonDiploid_annotated.txt"

    def specify_params(self):

      discovered = [
           constants.DONOR,
           constants.ONCOTREE,
           constants.TUMOUR_ID,
           constants.SEG_FILE
      ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')

      # Default parameters for priorities
      self.set_ini_default('configure_priority', 400)
      self.set_ini_default('extract_priority', 250)
      self.set_ini_default('render_priority', 700)

      # Default parameters for clinical, supplementary
      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)
      self.set_ini_default('attributes', 'clinical')

    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      
      # Get input_data.json if it exists; else return None
      input_data = self.workspace.read_maybe_input_params()
      for key in [constants.DONOR, constants.ONCOTREE, constants.TUMOUR_ID]:
            if wrapper.my_param_is_null(key):
                if input_data != None:
                    wrapper.set_my_param(key, input_data[key])
                else:
                    msg = "Cannot find {0} in manual config or input_params.json".format(key)
                    self.logger.error(msg)
                    raise RuntimeError(msg)

      # Get file from path_info.json
      wrapper = self.update_wrapper_if_null(
          wrapper,
          core_constants.DEFAULT_PATH_INFO,
          constants.SEG_FILE,
          constants.WF_ICHOR_SEG
      )

      return config 

    def extract(self, config):
      
      wrapper = self.get_config_wrapper(config)

      # Get the working directory
      work_dir = self.workspace.get_work_dir()

      # Get any input parameters
      tumour_id = config[self.identifier]['tumour_id']
      oncotree_code = config[self.identifier]['oncotree_code']

      # Get the seg file from the config
      seg_file = wrapper.get_my_string('seg_file')
      
      # Filter the seg_file only for amplifications (returns None if there are no amplifications)
      amp_path = preprocess(tumour_id, oncotree_code, work_dir).preprocess_seg(seg_file)

      cnv_data = {
          'plugin_name': 'Shallow Whole Genome Sequencing (sWGS)',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': {}
      }

      # Read purity
      with open(os.path.join(work_dir, 'purity.txt'), "r") as file:
          purity = float(file.readlines()[0])


      # Check purity
      if purity >= 0.1 and amp_path:

          # Preprocess the amplification data
          preprocess(tumour_id, oncotree_code, work_dir).run_R_code(amp_path)
          
          # Get the table rows
          rows = data_builder(work_dir).build_swgs_rows()
          
          # Put the information in the results section
          cnv_data['results'][constants.BODY] = rows
          cnv_data['results'][constants.CLINICALLY_RELEVANT_VARIANTS] = len(rows)
          cnv_data['results'][constants.PASS_TAR_PURITY] = True

          # Merge treatments (if there are any)
          cna_annotated_path = os.path.join(work_dir, self.CNA_ANNOTATED)
          cnv = data_builder(work_dir)
          cnv_data['merge_inputs'] = self.get_merge_inputs(work_dir)
          #cnv_data['merge_inputs']['treatment_options_merger'] =  cnv.build_therapy_info(cna_annotated_path, oncotree_code)
      
      elif purity >= 0.1 and not amp_path:
          
          # There will be no rows, so just set clinically relevant variants to 0, but still pass tar purity.
          cnv_data['results'][constants.CLINICALLY_RELEVANT_VARIANTS] = 0
          cnv_data['results'][constants.PASS_TAR_PURITY] = True
          
      else:
          cnv_data['results'][constants.PASS_TAR_PURITY] = False
      
      return cnv_data

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)


    def get_merge_inputs(self, work_dir):
      """
      Read gene and therapy information for merge inputs
      Both are derived from the annotated CNA file
      """
      # read the tab-delimited input file
      gene_info = []
      gene_info_factory = gim_factory(self.log_level, self.log_path)
      summaries = gene_summary_reader(self.log_level, self.log_path)
      treatments = []
      treatment_option_factory = tom_factory(self.log_level, self.log_path)
      input_name = self.CNA_ANNOTATED
      with open(os.path.join(work_dir, input_name)) as input_file:
          reader = csv.DictReader(input_file, delimiter="\t")
          for row_input in reader:
              # record the gene for all reportable alterations
              level = oncokb_levels.parse_oncokb_level(row_input)
              if level not in ['Unknown', 'NA']:
                  gene = row_input[constants.HUGO_SYMBOL_UPPER_CASE]
                  gene_info_entry = gene_info_factory.get_json(
                      gene=gene,
                      summary=summaries.get(gene)
                  )
                  gene_info.append(gene_info_entry)
              therapies = oncokb_levels.parse_actionable_therapies(row_input)
              # record therapy for all actionable alterations (OncoKB level 4 or higher)
              # row may contain therapies at multiple OncoKB levels
              for level in therapies.keys():
                  treatment_entry = treatment_option_factory.get_json(
                      tier = oncokb_levels.tier(level),
                      level = level,
                      gene = gene,
                      alteration = row_input['ALTERATION'],
                      alteration_url = None, # this field is not defined for CNVs
                      treatments = therapies[level]
                  )
                  treatments.append(treatment_entry)
      # assemble the output
      merge_inputs = {
          'gene_information_merger': gene_info,
          'treatment_options_merger': treatments
      }
      return merge_inputs

