"""
a plugin for WGTS SNV Indel
"""

# IMPORTS
import os
import csv
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
from djerba.util.render_mako import mako_renderer
import djerba.core.constants as core_constants
from djerba.core.workspace import workspace
import djerba.render.constants as rc
from djerba.extract.oncokb.annotator import oncokb_annotator
from djerba.util.subprocess_runner import subprocess_runner
from djerba.plugins.wgts.cnv_tools.preprocess import preprocess as process_cnv

class main(plugin_base):
   
    PRIORITY = 100
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'cnv_template.html'
    ASSAY = 'WGS'
    CNA_ANNOTATED = "purple.data_CNA_oncoKBgenes_nonDiploid_annotated.txt"
    ONCOLIST =  "data/20200818-oncoKBcancerGeneList.tsv"
    CENTROMERES = "data/hg38_centromeres.txt"

    def configure(self, config):
      config = self.apply_defaults(config)
      wrapper = self.get_config_wrapper(config)
      if wrapper.my_param_is_null('purity'):
        purity = get_purple_purity(config[self.identifier]['purple_purity_file'])
        wrapper.set_my_param('purity', purity[0])
      if wrapper.my_param_is_null('ploidy'):
        purity = get_purple_purity(config[self.identifier]['purple_purity_file'])
        wrapper.set_my_param('ploidy', purity[1])
      return wrapper.get_config()  

    def extract(self, config):
      wrapper = self.get_config_wrapper(config)  
      self.work_dir = self.workspace.get_work_dir()
      data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

      tumour_id = config[self.identifier]['tumour_id']
      normal_id = config[self.identifier]['normal_id'] 
      cbio_id = config[self.identifier]['cbio_id']
      ploidy = config[self.identifier]['ploidy']
      purity = config[self.identifier]['purity']
      oncotree_code = config[self.identifier]['oncotree_code']
      purple_gene_file = config[self.identifier]['purple_gene_file']
      purple_segment_file = config[self.identifier]['purple_segment_file']
      self.consider_purity_fit(config[self.identifier]['purple_purity_file'])

      cnv = process_cnv(self.work_dir)
      self.convert_purple_to_gistic(purple_gene_file, ploidy)
      self.tmp_dir = os.path.join(self.work_dir, 'tmp')
      oncokb_annotator(tumour_id, oncotree_code, self.work_dir, self.tmp_dir).annotate_cna(in_file_extension='purple.')
      data_table = cnv.build_copy_number_variation(self.ASSAY, self.CNA_ANNOTATED, oncotree_code)

      ## segments
      whizbam_url = construct_whizbam_link(cbio_id , tumour_id, normal_id )
      cnv_plot_base64 = self.analyze_segments(purple_segment_file, whizbam_url, purity, ploidy)
      data_table['cnv_plot']= cnv_plot_base64
      #data_table[ctc.PERCENT_GENOME_ALTERED] = cnv.calculate_percent_genome_altered(ctc.DATA_SEGMENTS)

      if self.ASSAY == "WGS":
        data_table['Has expression data']= False
      elif self.ASSAY == "WGTS":
        data_table['Has expression data']= True
        #TODO: add expression support

      data['results'] = data_table
      cna_annotated_path = os.path.join(self.work_dir, self.CNA_ANNOTATED)
      data['merge_inputs']['treatment_options_merger'] =  cnv.build_therapy_info(cna_annotated_path, oncotree_code)
      return data
    
    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)
    
    def specify_params(self):
      required = [
            'tumour_id',
            'oncotree_code',
            'purple_purity_file',
            'purple_segment_file',
            'purple_gene_file',
            'cbio_id',
            'normal_id'
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
      self.set_priority_defaults(self.PRIORITY)

    def consider_purity_fit(self, purple_range_file):
      dir_location = os.path.dirname(__file__)
      cmd = [
        'Rscript', os.path.join(dir_location + "/process_fit.r"),
        '--range_file', purple_range_file,
        '--outdir', self.work_dir
      ]
      runner = subprocess_runner()
      result = runner.run(cmd, "fit R script")
      return result

    def convert_purple_to_gistic(self, purple_gene_file, ploidy):
      dir_location = os.path.dirname(__file__)
      oncolistpath = os.path.join(dir_location, '../../..', self.ONCOLIST)
      cmd = [
        'Rscript', os.path.join(dir_location + "/process_CNA_data.r"),
        '--genefile', purple_gene_file,
        '--outdir', self.work_dir,
        '--oncolist', oncolistpath,
        '--ploidy', ploidy
      ]
      runner = subprocess_runner()
      result = runner.run(cmd, "CNA R script")
      return result
    
    def analyze_segments(self, segfile, whizbam_url, purity, ploidy):
      dir_location = os.path.dirname(__file__)
      centromeres_file = os.path.join(dir_location, '../../..', self.CENTROMERES)
      cmd = [
        'Rscript', os.path.join(dir_location + "/process_segment_data.r"),
        '--segfile', segfile,
        '--outdir', self.work_dir,
        '--centromeres', centromeres_file,
        '--purity', purity,
        '--ploidy', ploidy,
        '--whizbam_url', whizbam_url
      ]
      runner = subprocess_runner()
      result = runner.run(cmd, "segments R script")
      return result.stdout.split('"')[1]

def construct_whizbam_link(studyid, tumourid, normalid,  whizbam_base_url= 'https://whizbam.oicr.on.ca', seqtype= 'GENOME', genome= 'hg38'):
    whizbam = "".join((whizbam_base_url,
                        "/igv?project1=", studyid,
                        "&library1=", tumourid,
                        "&file1=", tumourid, ".bam",
                        "&seqtype1=", seqtype,
                        "&project2=", studyid,
                        "&library2=", normalid,
                        "&file2=", normalid, ".bam",
                        "&seqtype2=", seqtype,
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

