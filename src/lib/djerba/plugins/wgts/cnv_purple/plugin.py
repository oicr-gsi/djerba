"""
a plugin for WGTS CNV, based on PURPLE
"""

# IMPORTS
import os
import csv
from djerba.plugins.base import plugin_base, DjerbaPluginError
from mako.lookup import TemplateLookup
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
from djerba.core.workspace import workspace
from djerba.util.oncokb.annotator import oncokb_annotator
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.oncokb.annotator import annotator_factory

from djerba.plugins.wgts.cnv_purple.tools import process_purple
from djerba.plugins.cnv.tools import cnv_processor
import djerba.plugins.wgts.cnv_purple.constants as cpc 
import djerba.plugins.cnv.constants as cc
from djerba.helpers.input_params_helper.helper import main as input_params_helper


class main(plugin_base):
   
    PLUGIN_VERSION = '0.1.0'
    TEMPLATE_NAME = 'cnv_template.html'

    CONFIGURE = 80
    EXTRACT = 700
    RENDER = 800
    
    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)

      wrapper = self.fill_param_if_null(wrapper, 'assay', 'assay', input_params_helper.INPUT_PARAMS_FILE )
      wrapper = self.fill_param_if_null(wrapper, 'oncotree_code', 'oncotree code', input_params_helper.INPUT_PARAMS_FILE )
      wrapper = self.fill_param_if_null(wrapper, 'project', 'whizbam_project', input_params_helper.INPUT_PARAMS_FILE )

      wrapper = self.fill_param_if_null(wrapper, 'tumour_id', 'tumour_id', core_constants.DEFAULT_SAMPLE_INFO )
      wrapper = self.fill_file_if_null(wrapper, 'purple_purity', 'purple_purity_file', core_constants.DEFAULT_PATH_INFO)
      wrapper = self.fill_file_if_null(wrapper, 'purple_cnv', 'purple_cnv_file', core_constants.DEFAULT_PATH_INFO)
      wrapper = self.fill_file_if_null(wrapper, 'purple_segment', 'purple_segment_file', core_constants.DEFAULT_PATH_INFO)
      wrapper = self.fill_file_if_null(wrapper, 'purple_gene', 'purple_gene_file', core_constants.DEFAULT_PATH_INFO)

      if wrapper.my_param_is_null('purity'):
        purity = get_purple_purity(config[self.identifier]['purple_purity_file'])
        wrapper.set_my_param('purity', purity[0])
      if wrapper.my_param_is_null('ploidy'):
        purity = get_purple_purity(config[self.identifier]['purple_purity_file'])
        wrapper.set_my_param('ploidy', purity[1])

      purity_ploidy = {
           "purity" : config[self.identifier]['purity'],
           "ploidy" : config[self.identifier]['ploidy']
        }
      self.workspace.write_json("purity_ploidy.json", purity_ploidy)
      self.logger.debug("Wrote path info to workspace: {0}".format(purity_ploidy))

      return wrapper.get_config()  

    def extract(self, config):
      work_dir = self.workspace.get_work_dir()
      wrapper = self.get_config_wrapper(config)  
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

      tumour_id = config[self.identifier]['tumour_id']
      ploidy = config[self.identifier]['ploidy']
      oncotree_code = config[self.identifier]['oncotree code']

      tmp_dir = self.make_and_check_tmp(work_dir)
      purple_cnv = process_purple(work_dir, tmp_dir)
      purple_cnv.consider_purity_fit(work_dir, config[self.identifier]['purple_purity_file'])
      purple_cnv.convert_purple_to_gistic(work_dir, config[self.identifier]['purple_gene_file'], ploidy)
      cnv_plot_base64 = purple_cnv.analyze_segments(config[self.identifier]['purple_cnv_file'], 
                                                    config[self.identifier]['purple_segment_file'], 
                                                    construct_whizbam_link(config[self.identifier]['whizbam_project'] , tumour_id ),
                                                    config[self.identifier]['purity'], 
                                                    ploidy)
      if os.path.exists(core_constants.DEFAULT_PATH_INFO):
        purple_alternate = purple_cnv.write_purple_alternate_launcher(self.workspace.read_json(core_constants.DEFAULT_PATH_INFO))
        self.workspace.write_json("purple.alternate.json", purple_alternate)
      oncokb_annotator(tumour_id, oncotree_code, work_dir, tmp_dir).annotate_cna()
      cnv = cnv_processor(work_dir, wrapper, self.log_level, self.log_path)
      data['results'] = cnv.get_results()
      data['results']['cnv plot']= cnv_plot_base64
      data['merge_inputs'] = cnv.get_merge_inputs()

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

    def fill_param_if_null(self, wrapper, param, ini_param, input_param_file):
        if wrapper.my_param_is_null(ini_param):
            if self.workspace.has_file(input_param_file):
                data = self.workspace.read_json(input_param_file)
                param_value = data[param]
                wrapper.set_my_param(ini_param, param_value)
            else:
                msg = "Cannot find {0}; must be manually specified or ".format(ini_param)+\
                        "given in {0}".format(input_param_file)
                self.logger.error(msg)
                raise DjerbaPluginError(msg)
        return(wrapper)

    def make_and_check_tmp(self, work_dir):
      tmp_dir = os.path.join(work_dir, 'tmp')
      if os.path.isdir(tmp_dir):
          print("Using tmp dir {0} for R script wrapper".format(tmp_dir))
          self.logger.debug("Using tmp dir {0} for R script wrapper".format(tmp_dir))
      elif os.path.exists(tmp_dir):
          msg = "tmp dir path {0} exists but is not a directory".format(tmp_dir)
          self.logger.error(msg)
          raise RuntimeError(msg)
      else:
          print("Creating tmp dir {0} for R script wrapper".format(tmp_dir))
          self.logger.debug("Creating tmp dir {0} for R script wrapper".format(tmp_dir))
          os.mkdir(tmp_dir)
      return(tmp_dir)

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
      discovered = [
            'assay',
            'whizbam_project',
            'oncotree code',
            'tumour_id',
            'purple_purity_file',
            'purple_cnv_file',
            'purple_gene_file',
            'purple_segment_file',
            'purity',
            'ploidy'
        ]
      for key in discovered:
          self.add_ini_discovered(key)
      self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
      self.set_ini_default(core_constants.CONFIGURE_PRIORITY, self.CONFIGURE)
      self.set_ini_default(core_constants.EXTRACT_PRIORITY, self.EXTRACT)
      self.set_ini_default(core_constants.RENDER_PRIORITY, self.RENDER)

def construct_whizbam_link(studyid, tumourid,  whizbam_base_url= 'https://whizbam.oicr.on.ca', seqtype= 'GENOME', genome= 'hg38'):
    whizbam = "".join((whizbam_base_url,
                        "/igv?project1=", studyid,
                        "&library1=", tumourid,
                        "&file1=", tumourid, ".bam",
                        "&seqtype1=", seqtype,
                        "&genome=", genome
                        ))
    return(whizbam)

def get_purple_purity(purple_purity_path):
  with open(purple_purity_path, 'r') as purple_purity_file:
      purple_purity = csv.reader(purple_purity_file, delimiter="\t")
      header=True
      purity = []
      ploidy = []
      for row in purple_purity:
          if header:
             header=False
          else:
            try: 
                purity.append(row[0])
                ploidy.append(row[4])
            except IndexError as err:
                msg = "Incorrect number of columns in PURPLE Purity file: '{0}'".format(purple_purity_path)
                raise RuntimeError(msg) from err
  return [float(purity[0]), float(ploidy[0])]

