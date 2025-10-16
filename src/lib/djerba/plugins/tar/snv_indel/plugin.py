import os
import csv
import pandas as pd
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.tar.snv_indel.constants as constants
from djerba.plugins.tar.snv_indel.snv_indel_tools.preprocess import preprocess
from djerba.plugins.tar.snv_indel.snv_indel_tools.extract import data_builder as data_extractor 
import djerba.core.constants as core_constants
import djerba.plugins.tar.snv_indel.snv_indel_tools.constants as sic
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
from djerba.core.workspace import workspace
from djerba.util.render_mako import mako_renderer
from djerba.util.html import html_builder as hb
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.util.environment import directory_finder
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.oncokb.tools import gene_summary_reader

class main(plugin_base):
   
    PRIORITY = 600
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'html/snv_indel_template.html'
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
         
    def specify_params(self):

      discovered = [
           constants.DONOR,
           constants.ONCOTREE,
           constants.ASSAY,
           constants.CBIO_ID,
           constants.TUMOUR_ID,
           constants.NORMAL_ID,
           constants.MAF_FILE,
      ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
      self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      # Get input_data.json if it exists; else return None
      input_data = self.workspace.read_maybe_input_params()
      # FIRST PASS: get input parameters
      for key in [
          constants.NORMAL_ID,
          constants.TUMOUR_ID,
          constants.CBIO_ID,
          constants.ONCOTREE,
          constants.ASSAY,
          constants.DONOR
      ]:
          if wrapper.my_param_is_null(key):
              if input_data != None:
                  wrapper.set_my_param(key, input_data[key])
              else:
                  msg = "Cannot find {0} in manual config or input_params.json".format(key)
                  self.logger.error(msg)
                  raise RuntimeError(msg)
      

      # Get files from path_info.json
      wrapper = self.update_wrapper_if_null(
          wrapper,
          core_constants.DEFAULT_PATH_INFO,
          constants.MAF_FILE,
          constants.WF_MAF
      )
      return config  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)
      
      # Get the working directory
      work_dir = self.workspace.get_work_dir()

      # Get any input parameters
      oncotree_code = config[self.identifier][constants.ONCOTREE]
      cbio_id = config[self.identifier][constants.CBIO_ID]
      tumour_id = config[self.identifier][constants.TUMOUR_ID]
      normal_id = config[self.identifier][constants.NORMAL_ID]
      assay = config[self.identifier][constants.ASSAY]

      # Get starting plugin data
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
      
      # Get purity only if the file exists
      if self.workspace.has_file('purity.txt'):
          with open(os.path.join(work_dir, 'purity.txt'), "r") as file:
              purity = float(file.readlines()[0]) 
      else:
          purity = 0 # just needs to be anything less than 10% to ignore copy state

      maf_file = self.filter_for_panel_genes(work_dir, config[self.identifier][constants.MAF_FILE])
      preprocess(config, work_dir, assay, oncotree_code, cbio_id, tumour_id, normal_id, maf_file).run_R_code()
      
      mutations_file = os.path.join(work_dir, sic.MUTATIONS_EXTENDED)
      mutations_extended_file = os.path.join(work_dir, sic.MUTATIONS_EXTENDED_ONCOGENIC)
      
      output_data = data_extractor(work_dir, assay, oncotree_code).build_small_mutations_and_indels(mutations_extended_file)
      results = {
           sic.CLINICALLY_RELEVANT_VARIANTS: len(output_data),
           sic.TOTAL_VARIANTS: data_extractor(work_dir, assay, oncotree_code).read_somatic_mutation_totals(mutations_file),
           sic.HAS_EXPRESSION_DATA: False,
           sic.BODY: output_data
      }
      if purity >= 0.1:
          results[sic.PASS_TAR_PURITY] = True
      else:
          results[sic.PASS_TAR_PURITY] = False
      data['results'] = results

      mutations_annotated_path = os.path.join(work_dir, sic.MUTATIONS_EXTENDED_ONCOGENIC)
      data['merge_inputs'] = self.get_merge_inputs(work_dir, oncotree_code)
      return data

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)


    def filter_for_panel_genes(self, work_dir, maf_path):
      """
      Mutect2Consensus does NOT filter for the list of genes in tar constants.py
      We still need to filter for just the genes on the panel.
      """
      df_pl = pd.read_csv(maf_path,
                      sep = "\t",
                      on_bad_lines="error",
                      compression='gzip')

      for row in df_pl.iterrows():
          hugo_symbol = row[1]['Hugo_Symbol']
          if hugo_symbol not in constants.GENES_TO_KEEP:
              df_pl = df_pl.drop(row[0])  

      out_path = os.path.join(work_dir, 'panel_genes_only.maf.gz')
      df_pl.to_csv(out_path, sep = "\t", compression='gzip', index=False)
      return out_path

    def get_merge_inputs(self, work_dir, oncotree_code):
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
      input_name = sic.MUTATIONS_EXTENDED_ONCOGENIC
      with open(os.path.join(work_dir, input_name)) as input_file:
          reader = csv.DictReader(input_file, delimiter="\t")
          for row_input in reader:
              # record the gene for all reportable alterations
              level = oncokb_levels.parse_oncokb_level(row_input)
              if level not in ['Unknown', 'NA']:
                  gene = row_input[sic.HUGO_SYMBOL_TITLE_CASE]
                  gene_info_entry = gene_info_factory.get_json(
                      gene=gene,
                      summary=summaries.get(gene)
                  )
                  gene_info.append(gene_info_entry)
              # record therapy for all actionable alterations (OncoKB level 4 or higher)
              therapies = oncokb_levels.parse_actionable_therapies(row_input)
              for level in therapies.keys():
                  alteration = row_input[sic.HGVSP_SHORT]
                  alteration_url = hb.build_alteration_url(gene, alteration, oncotree_code)
                  if gene == 'BRAF' and alteration == 'p.V640E':
                      alteration = 'p.V600E'
                  if 'splice' in row_input[sic.VARIANT_CLASSIFICATION].lower():
                      alteration = 'p.? (' + row_input[sic.HGVSC] + ')'
                      alteration_url = hb.build_alteration_url(gene, "Truncating%20Mutations", oncotree_code)
                  treatment_entry = treatment_option_factory.get_json(
                      tier = oncokb_levels.tier(level),
                      level = level,
                      gene = gene,
                      alteration = alteration,
                      alteration_url = alteration_url,
                      treatments = therapies[level]
                  )
                  treatments.append(treatment_entry)
      # assemble the output
      merge_inputs = {
          'gene_information_merger': gene_info,
          'treatment_options_merger': treatments
      }
      return merge_inputs
