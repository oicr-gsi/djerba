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
from djerba.util.render_mako import mako_renderer
import djerba.util.input_params_tools as input_params_tools

class main(plugin_base):
   
    PRIORITY = 300
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
           'tumour_id',
           'normal_id',
           'project',
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
      workspace = self.workspace

      # Get input_data.json if it exists; else return None
      input_data = input_params_tools.get_input_params_json(workspace)


      # FIRST PASS: get input parameters
      if wrapper.my_param_is_null('donor'):
          wrapper.set_my_param('donor', input_data['donor'])
      if wrapper.my_param_is_null('assay'):
          wrapper.set_my_param('assay', input_data['assay'])
      if wrapper.my_param_is_null('oncotree_code'):
          wrapper.set_my_param('oncotree_code', input_data['oncotree_code'])
      if wrapper.my_param_is_null('tumour_id'):
          wrapper.set_my_param('tumour_id', input_data['tumour_id'])
      if wrapper.my_param_is_null('normal_id'):
          wrapper.set_my_param('normal_id', input_data['normal_id'])
      if wrapper.my_param_is_null('project'):
          wrapper.set_my_param('project', input_data['project'])
      
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
      project = config[self.identifier]["project"]
      oncotree_code = config[self.identifier]["oncotree_code"]
      tumour_id = config[self.identifier]["tumour_id"]
      normal_id = config[self.identifier]["normal_id"]
      assay = config[self.identifier]["assay"]

      # Get starting plugin data
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)
      
      # Get purity
      with open(os.path.join(work_dir, 'purity.txt'), "r") as file:
            purity = float(file.readlines()[0]) 
      
      # Preprocessing
      maf_file = self.filter_maf_for_tar(work_dir, config[self.identifier]["maf_file"], config[self.identifier]["maf_file_normal"])
      preprocess(config, work_dir, assay, project, oncotree_code, tumour_id, normal_id, maf_file).run_R_code()
      
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
      data['merge_inputs']['treatment_options_merger'] =  data_extractor(work_dir, assay, oncotree_code).build_therapy_info(mutations_annotated_path, oncotree_code)
      return data

    def render(self, data):
      renderer = mako_renderer(self.get_module_dir())
      return renderer.render_name(self.TEMPLATE_NAME, data)
      #args = data
      #html_dir = os.path.realpath(os.path.join(
      #    os.path.dirname(__file__),
      #    'html'
      #))
      #report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
      #mako_template = report_lookup.get_template(self.TEMPLATE_NAME)
      #try:
      #    html = mako_template.render(**args)
      #except Exception as err:
      #    msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
      #    self.logger.error(msg)
      #    raise
      #return html


    def get_maf_file(self, donor, results_suffix):
      """
      pull data from results file
      """
      provenance = provenance_tools.subset_provenance(self, self.WORKFLOW, donor)
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
                            ((df_freq['Tumor_Seq_Allele'] == row[1][11]) |
                            (df_freq['Tumor_Seq_Allele'] == row[1][12]))]

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

