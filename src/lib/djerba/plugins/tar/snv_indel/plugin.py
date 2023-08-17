"""
Plugin for TAR SNV Indel
"""

# IMPORTS
import os
import pandas as pd
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.snv_indel_tools.constants as constants
import djerba.plugins.tar.snv_indel.constants as tar_constants
from djerba.snv_indel_tools.preprocess import preprocess
from djerba.snv_indel_tools.extract import data_builder as data_extractor 
import djerba.core.constants as core_constants
import djerba.snv_indel_tools.constants as sic
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
import djerba.plugins.tar.provenance_tools as provenance_tools
from djerba.core.workspace import workspace

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'snv_indel_template.html'
    WORKFLOW = 'consensusCruncher'
    RESULTS_SUFFIX_Pl = 'Pl.merged.maf.gz'
    RESULTS_SUFFIX_BC = 'BC.merged.maf.gz'
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
         
    def specify_params(self):
      self.add_ini_required('maf_file')
      self.add_ini_required('maf_file_normal')
      self.add_ini_required('oncotree_code')
      self.add_ini_required('tcgacode')
      self.add_ini_required('tumour_id')
      self.add_ini_required('normal_id')
      self.add_ini_required('root_sample_name')
      self.add_ini_required('study_title')

      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)
      self.set_ini_default('attributes', 'clinical')
      self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):
      config = self.apply_defaults(config)

      # Populate ini
      config[self.identifier]["maf_file"] = self.get_maf_file(config[self.identifier]["root_sample_name"], self.RESULTS_SUFFIX_Pl)
      config[self.identifier]["maf_file_normal"] = self.get_maf_file(config[self.identifier]["root_sample_name"], self.RESULTS_SUFFIX_BC)
      
      return config  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)
      work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

      maf_file = self.filter_maf_for_tar(work_dir, config[self.identifier]["maf_file"], config[self.identifier]["maf_file_normal"])
      oncotree = config[self.identifier]["oncotree_code"]
      assay = "TAR"
      preprocess(config, work_dir, maf_file, tar=True).run_R_code()
      mutations_file = os.path.join(work_dir, sic.MUTATIONS_EXTENDED)
      mutations_extended_file = os.path.join(work_dir, sic.MUTATIONS_EXTENDED_ONCOGENIC)
      
      output_data = data_extractor(work_dir, assay, oncotree).build_small_mutations_and_indels(mutations_extended_file)
      results = {
           sic.CLINICALLY_RELEVANT_VARIANTS: len(data),
           sic.TOTAL_VARIANTS: data_extractor(work_dir, assay, oncotree).read_somatic_mutation_totals(mutations_file),
           sic.HAS_EXPRESSION_DATA: False,
           sic.BODY: output_data
      }
      data['results'] = results
      return data

    #def extract(self, config):
    #  
    #  wrapper = self.get_config_wrapper(config)  
    #  work_dir = self.workspace.get_work_dir()
#
    #  # Pre-processing
    #  maf_file = self.filter_maf_for_tar(work_dir, config[self.identifier]["maf_file"], config[self.identifier]["maf_file_normal"])
    #  oncotree = config[self.identifier]["oncotree_code"]
    #  preprocess(config, work_dir, maf_file, tar=True).run_R_code()

     # data = {
     #     'plugin_name': 'Tar SNV Indel',
     #     'version': self.PLUGIN_VERSION,
     #     'priorities': wrapper.get_my_priorities(),
     #     'attributes': wrapper.get_my_attributes(),
     #     'merge_inputs': {},
     #     'results': data_builder(work_dir, oncotree).build_small_mutations_and_indels()
     # }
     # return data

    def render(self, data):
      args = data
      html_dir = os.path.realpath(os.path.join(
          os.path.dirname(__file__),
          'html'
      ))
      report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
      mako_template = report_lookup.get_template(self.TEMPLATE_NAME)
      try:
          html = mako_template.render(**args)
      except Exception as err:
          msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
          self.logger.error(msg)
          raise
      return html


    def get_maf_file(self, root_sample_name, results_suffix):
      """
      pull data from results file
      """
      provenance = provenance_tools.subset_provenance(self, self.WORKFLOW, root_sample_name)
      try:
          results_path = provenance_tools.parse_file_path(self, results_suffix, provenance)
      except OSError as err:
          msg = "File with extension {0} not found".format(results_suffix)
          raise RuntimeError(msg) from err
      return results_path

    def filter_maf_for_tar(self, work_dir, maf_path, maf_file_normal):

      df_bc = pd.read_csv(maf_file_normal,
                      sep = "\t",
                      on_bad_lines="error",
                      compression='gzip',
                      skiprows=[0],
                      index_col = 34)

      df_pl = pd.read_csv(maf_path,
                      sep = "\t",
                      on_bad_lines="error",
                      compression='gzip',
                      skiprows=[0])
      df_freq = pd.read_csv(os.path.join(os.environ.get('DJERBA_BASE_DIR'), tar_constants.FREQUENCY_FILE),
                   sep = "\t")
       
      for row in df_pl.iterrows():
          hugo_symbol = row[1][0]
          hgvsp_short = row[1][34]
     
          """"For normal values"""
          try:
              if hgvsp_short in df_bc.index:
                  df_pl.at[row[0], "n_depth"] = df_bc.loc[hgvsp_short]["n_depth"]
                  df_pl.at[row[0], "n_ref_count"] = df_bc.loc[hgvsp_short]["n_ref_count"]
                  df_pl.at[row[0], "n_alt_count"] = df_bc.loc[hgvsp_short]["n_alt_count"]
              else:
                  df_pl.at[row[0], "n_depth"] = 0
                  df_pl.at[row[0], "n_ref_count"] = 0
                  df_pl.at[row[0], "n_alt_count"] = 0
          except:
              df_pl.at[row[0], "n_depth"] = 0
              df_pl.at[row[0], "n_ref_count"] = 0
              df_pl.at[row[0], "n_alt_count"] = 0
            
          """"For frequency values"""    
          
          row_lookup = df_freq[(df_freq['Start_Position'] == row[1][5]) & 
                            (df_freq['Reference_Allele'] == row[1][10]) & 
                            (df_freq['Tumor_Seq_Allele2'] == row[1][11])]
        
          if len(row_lookup) > 0:
              df_pl.at[row[0], 'Freq'] = row_lookup['Freq'].item()
          else:
              df_pl.at[row[0], 'Freq'] = 0
    
      for row in df_pl.iterrows():
          hugo_symbol = row[1][0]
          frequency = row[1][118]
          n_alt_count = row[1][44]
          gnomadAD_AF = row[1][104]
          if hugo_symbol not in tar_constants.GENES_TO_KEEP or frequency > 0.1 or n_alt_count > 4 or gnomadAD_AF > 0.001:
              df_pl = df_pl.drop(row[0])  

      out_path = os.path.join(work_dir, 'filtered_maf_for_tar.maf.gz')
      df_pl.to_csv(out_path, sep = "\t", compression='gzip', index=False)
      return out_path

