import os
import csv
import pandas as pd
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.tar.snv_indel.snv_indel_tools.constants as constants
import djerba.plugins.tar.snv_indel.constants as tar_constants
from djerba.plugins.tar.snv_indel.snv_indel_tools.preprocess import preprocess
from djerba.plugins.tar.snv_indel.snv_indel_tools.extract import data_builder as data_extractor 
import djerba.core.constants as core_constants
import djerba.plugins.tar.snv_indel.snv_indel_tools.constants as sic
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
from djerba.plugins.tar.provenance_tools import parse_file_path
from djerba.plugins.tar.provenance_tools import subset_provenance
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
    WORKFLOW = 'consensusCruncher'
    RESULTS_SUFFIX_Pl = 'Pl.merged.maf.gz'
    RESULTS_SUFFIX_BC = 'BC.merged.maf.gz'
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
         
    def specify_params(self):

      discovered = [
           'donor',
           'oncotree_code',
           'assay',
           'cbio_id',
           'tumour_id',
           'normal_id',
           'maf_file',
           'maf_file_normal',
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
          'normal_id',
          'tumour_id',
          'cbio_id',
          'oncotree_code',
          'assay',
          'donor'
      ]:
          if wrapper.my_param_is_null(key):
              if input_data != None:
                  wrapper.set_my_param(key, input_data[key])
              else:
                  msg = "Cannot find {0} in manual config or input_params.json".format(key)
                  self.logger.error(msg)
                  raise RuntimeError(msg)
      
      # SECOND PASS: get files
      if wrapper.my_param_is_null('maf_file'):
          wrapper.set_my_param("maf_file", self.get_maf_file(config[self.identifier]['donor'], self.RESULTS_SUFFIX_Pl))
      if wrapper.my_param_is_null('maf_file_normal'):
          wrapper.set_my_param("maf_file_normal", self.get_maf_file(config[self.identifier]['donor'], self.RESULTS_SUFFIX_BC))
      return config  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)
      
      # Get the working directory
      work_dir = self.workspace.get_work_dir()

      # Get any input parameters
      oncotree_code = config[self.identifier]["oncotree_code"]
      cbio_id = config[self.identifier]["cbio_id"]
      tumour_id = config[self.identifier]["tumour_id"]
      normal_id = config[self.identifier]["normal_id"]
      assay = config[self.identifier]["assay"]

      # Get starting plugin data
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
      
      # Get purity only if the file exists
      if self.workspace.has_file('purity.txt'):
          with open(os.path.join(work_dir, 'purity.txt'), "r") as file:
              purity = float(file.readlines()[0]) 
      else:
          purity = 0 # just needs to be anything less than 10% to ignore copy state

      # Preprocessing
      maf_file = self.filter_maf_for_tar(work_dir, config[self.identifier]["maf_file"], config[self.identifier]["maf_file_normal"])
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

    def get_maf_file(self, donor, results_suffix):
      """
      pull data from results file
      """
      provenance = subset_provenance(self, self.WORKFLOW, donor)
      try:
          results_path = parse_file_path(self, results_suffix, provenance)
      except OSError as err:
          msg = "File with extension {0} not found".format(results_suffix)
          raise RuntimeError(msg) from err
      return results_path

    def filter_maf_for_tar(self, work_dir, maf_path, maf_file_normal):

      df_bc = pd.read_csv(maf_file_normal,
                      sep = "\t",
                      on_bad_lines="error",
                      compression='gzip',
                      skiprows=[0])

      df_pl = pd.read_csv(maf_path,
                      sep = "\t",
                      on_bad_lines="error",
                      compression='gzip',
                      skiprows=[0])
      base_dir = directory_finder(self.log_level, self.log_path).get_base_dir()
      df_freq = pd.read_csv(os.path.join(base_dir, tar_constants.FREQUENCY_FILE),
                   sep = "\t")

      # Need to clean up the tumour and normal dataframes
      for column in tar_constants.CLEAN_COLUMNS:
          # Convert to numeric, setting errors='coerce' to turn non-numeric values into NaN
          df_pl[column] = pd.to_numeric(df_pl[column], errors='coerce')
          df_bc[column] = pd.to_numeric(df_bc[column], errors='coerce')
          # Replace NaN with 0
          df_pl[column] = df_pl[column].fillna(0)
          df_bc[column] = df_bc[column].fillna(0)

      for row in df_pl.iterrows():
          hugo_symbol = row[1]['Hugo_Symbol']
          chromosome = row[1]['Chromosome']
          start_position = row[1]['Start_Position']
          reference_allele = row[1]['Reference_Allele']
          allele = row[1]['Allele']

          """"For normal values"""

          # Lookup the entry in the BC
          row_lookup = df_bc[(df_bc['Hugo_Symbol'] == hugo_symbol) & 
                                 (df_bc['Chromosome'] == chromosome) & 
                                 (df_bc['Start_Position'] == start_position) &
                                 (df_bc['Reference_Allele'] == reference_allele) &
                                 (df_bc['Allele'] == allele)]

          # If there's only one entry, take its normal values
          if len(row_lookup) == 1:
              df_pl.at[row[0], "n_depth"] = row_lookup['n_depth'].item()
              df_pl.at[row[0], "n_ref_count"] = row_lookup['n_ref_count'].item()
              df_pl.at[row[0], "n_alt_count"] = row_lookup['n_alt_count'].item()
          
          # If the entry isn't in the table, 
          # or if there is more than one value and so you can't choose which normal values to take, 
          # set them as 0
          else:
              df_pl.at[row[0], "n_depth"] = 0
              df_pl.at[row[0], "n_ref_count"] = 0
              df_pl.at[row[0], "n_alt_count"] = 0

          """"For frequency values"""    
          
          row_lookup = df_freq[(df_freq['Start_Position'] == row[1]['Start_Position']) &
                            (df_freq['Reference_Allele'] == row[1]['Reference_Allele']) &
                            ((df_freq['Tumor_Seq_Allele'] == row[1]['Tumor_Seq_Allele1']) |
                            (df_freq['Tumor_Seq_Allele'] == row[1]['Tumor_Seq_Allele2']))]

          if len(row_lookup) > 0:
              df_pl.at[row[0], 'Freq'] = row_lookup['Freq'].item()
          else:
              df_pl.at[row[0], 'Freq'] = 0
    
      for row in df_pl.iterrows():
          hugo_symbol = row[1]['Hugo_Symbol']
          frequency = row[1]['Freq']
          n_alt_count = row[1]['n_alt_count']
          gnomAD_AF = row[1]['gnomAD_AF']
          if hugo_symbol not in tar_constants.GENES_TO_KEEP or frequency > 0.1 or n_alt_count > 4 or gnomAD_AF > 0.001:
              df_pl = df_pl.drop(row[0])  

      out_path = os.path.join(work_dir, 'filtered_maf_for_tar.maf.gz')
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
      input_name = constants.MUTATIONS_EXTENDED_ONCOGENIC
      with open(os.path.join(work_dir, input_name)) as input_file:
          reader = csv.DictReader(input_file, delimiter="\t")
          for row_input in reader:
              # record the gene for all reportable alterations
              level = oncokb_levels.parse_oncokb_level(row_input)
              if level not in ['Unknown', 'NA']:
                  gene = row_input[constants.HUGO_SYMBOL_TITLE_CASE]
                  gene_info_entry = gene_info_factory.get_json(
                      gene=gene,
                      summary=summaries.get(gene)
                  )
                  gene_info.append(gene_info_entry)
              # record therapy for all actionable alterations (OncoKB level 4 or higher)
              therapies = oncokb_levels.parse_actionable_therapies(row_input)
              for level in therapies.keys():
                  alteration = row_input[constants.HGVSP_SHORT]
                  alteration_url = hb.build_alteration_url(gene, alteration, oncotree_code)
                  if gene == 'BRAF' and alteration == 'p.V640E':
                      alteration = 'p.V600E'
                  if 'splice' in row_input[constants.VARIANT_CLASSIFICATION].lower():
                      alteration = 'p.? (' + row_input[constants.HGVSC] + ')'
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
