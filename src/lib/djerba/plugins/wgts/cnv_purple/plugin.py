"""
a plugin for WGTS CNV, based on PURPLE
"""

# IMPORTS
import os
import csv
from djerba.plugins.base import plugin_base
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

class main(plugin_base):
   
    PLUGIN_VERSION = '0.1.0'
    TEMPLATE_NAME = 'cnv_template.html'

    CONFIGURE = 800
    EXTRACT = 700
    RENDER = 800
    
    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)

      #TODO: integrate input_params_helper
      if wrapper.my_param_is_null('purity'):
        purity = get_purple_purity(config[self.identifier]['purple_purity_file'])
        wrapper.set_my_param('purity', purity[0])
      if wrapper.my_param_is_null('ploidy'):
        purity = get_purple_purity(config[self.identifier]['purple_purity_file'])
        wrapper.set_my_param('ploidy', purity[1])
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
      cnv_plot_base64 = purple_cnv.analyze_segments(config[self.identifier]['purple_segment_file'], 
                                                    construct_whizbam_link(config[self.identifier]['cbio_id'] , tumour_id ),
                                                    config[self.identifier]['purity'], 
                                                    ploidy)

      oncokb_annotator(tumour_id, oncotree_code, work_dir, tmp_dir).annotate_cna()
      cnv = cnv_processor(work_dir, wrapper, self.log_level, self.log_path)
      data['results'] = cnv.get_results()
      data['results']['cnv plot']= cnv_plot_base64
      data['merge_inputs'] = cnv.get_merge_inputs()

      return data
    
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
      required = [
            'tumour_id',
            'oncotree code',
            'purple_purity_file',
            'purple_segment_file',
            'purple_gene_file',
            'cbio_id',
            'assay'
          ]
      for key in required:
          self.add_ini_required(key)
      discovered = [
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

