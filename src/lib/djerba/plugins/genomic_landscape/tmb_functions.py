
import base64
import csv
import logging
import os
import djerba.plugins.genomic_landscape.constants as constants
from djerba.util.logger import logger
from djerba.util.image_to_base64 import converter
from djerba.util.subprocess_runner import subprocess_runner
from statsmodels.distributions.empirical_distribution import ECDF


def run(genomic_landscape_plugin, work_dir, data_dir, r_script_dir, tcga_code, biomarkers_path, tumour_id, tmb_value=None):
        genomic_landscape_info = build_genomic_landscape_info(genomic_landscape_plugin, work_dir, data_dir, tcga_code)
        if tmb_value == None:
            tmb_value = genomic_landscape_info[constants.TMB_PER_MB]
        tmb_dict = call_TMB(genomic_landscape_plugin, tmb_value)
        tmb_plot_location = write_biomarker_plot(genomic_landscape_plugin, work_dir, r_script_dir, tcga_code, "tmb", tmb = tmb_value)
        tmb_dict[constants.METRIC_PLOT] = converter().convert_svg(tmb_plot_location, 'TMB plot')

        data = {
                constants.GENOMIC_LANDSCAPE_INFO: genomic_landscape_info,
                constants.BIOMARKERS: {constants.TMB: tmb_dict}
        }

        # Write to genomic biomarkers maf if MSI is actionable
        if data[constants.BIOMARKERS][constants.TMB][constants.METRIC_ACTIONABLE]:
            with open(biomarkers_path, "a") as biomarkers_file:
                row = '\t'.join([constants.HUGO_SYMBOL, tumour_id, data[constants.BIOMARKERS][constants.TMB][constants.METRIC_ALTERATION]])
                biomarkers_file.write(row + "\n")


        return(data)

def build_genomic_landscape_info(genomic_landscape_plugin, work_dir, data_dir, tcga_code):
        # need to calculate TMB and percentiles
        cohort = read_cohort(genomic_landscape_plugin, data_dir, tcga_code)
        data = {}
        tmb_count = get_tmb_count(genomic_landscape_plugin, work_dir)
        data[constants.TMB_TOTAL] = tmb_count
        data[constants.TMB_PER_MB] = round(tmb_count/constants.V7_TARGET_SIZE, 2)
        data[constants.PERCENT_GENOME_ALTERED] = int(round(read_fga(work_dir)*100, 0))
        csp = read_cancer_specific_percentile(genomic_landscape_plugin, data_dir, data[constants.TMB_PER_MB], cohort, tcga_code)
        data[constants.CANCER_SPECIFIC_PERCENTILE] = csp
        data[constants.CANCER_SPECIFIC_COHORT] = cohort
        pcp = read_pan_cancer_percentile(genomic_landscape_plugin, data_dir, data[constants.TMB_PER_MB])
        data[constants.PAN_CANCER_PERCENTILE] = int(round(pcp, 0))
        data[constants.PAN_CANCER_COHORT] = constants.PAN_CANCER_COHORT_VALUE
        return data


def call_TMB(genomic_landscape_plugin, tmb_value):
        tmb_dict = {constants.ALT: constants.TMB,
                    constants.ALT_URL: "https://www.oncokb.org/gene/Other%20Biomarkers/TMB-H",
                    constants.METRIC_VALUE: tmb_value
                    }
        if tmb_value >= 10:
            tmb_dict[constants.METRIC_ACTIONABLE] = True
            tmb_dict[constants.METRIC_ALTERATION] = "TMB-H"
            tmb_dict[constants.METRIC_TEXT] = "Tumour Mutational Burden High (TMB-H, &#8805 10 coding mutations / Mb)"
        elif tmb_value < 10:
            tmb_dict[constants.METRIC_ACTIONABLE] = False
            tmb_dict[constants.METRIC_ALTERATION] = "TMB-L"
            tmb_dict[constants.METRIC_TEXT] = "Tumour Mutational Burden Low (TMB-L, < 10 coding mutations / Mb)"
        else:
            msg = "TMB value from landscape info is not a number"
            genomic_landscape_plugin.logger.error(msg)
            raise RuntimeError(msg)
        return(tmb_dict)


def read_cancer_specific_percentile(genomic_landscape_plugin, data_dir, tmb, cohort, cancer_type):
        # Read percentile for given TMB/Mb and cohort
        # We use statsmodels to compute the ECDF
        # See: https://stackoverflow.com/a/15792672
        # Introduces dependency on Pandas, but still the most convenient solution
        if cohort == constants.NA:
            percentile = constants.NA
        else:
            if cohort == constants.COMPASS:
                data_filename = constants.TMBCOMP_EXTERNAL
            else:
                data_filename = constants.TMBCOMP_TCGA
            tmb_array = []
            with open(os.path.join(data_dir, data_filename)) as data_file:
                for row in csv.DictReader(data_file, delimiter="\t"):
                    if row[constants.CANCER_TYPE_HEADER] == cancer_type:
                        tmb_array.append(float(row[constants.TMB_HEADER]))
            ecdf = ECDF(tmb_array)
            percentile = int(round(ecdf(tmb)*100, 0)) # return an integer percentile
        return percentile

def read_cohort(genomic_landscape_plugin, data_dir, tcga_code):
        # cohort is:
        # 1) COMPASS if 'closest TCGA' is paad
        # 2) CANCER.TYPE from tmbcomp-tcga.txt if one matches 'closest TCGA'
        # 3) NA otherwise
        #
        # Note: cohort in case (1) is really the Source column in tmbcomp-externaldata.txt
        # but for now this only has one value
        # TODO need to define a procedure for adding more data cohorts
        tcga_cancer_types = set()
        with open(os.path.join(data_dir, constants.TMBCOMP_TCGA)) as tcga_file:
            reader = csv.reader(tcga_file, delimiter="\t")
            for row in reader:
                tcga_cancer_types.add(row[3])
        if tcga_code.lower() == 'paad':
            cohort = constants.COMPASS
        elif tcga_code.lower() in tcga_cancer_types: 
            cohort = "".join(("TCGA ", tcga_code.upper()))
        else:
            cohort = constants.NA
        return cohort

def read_fga(work_dir):
        input_path = os.path.join(work_dir, constants.DATA_SEGMENTS)
        total = 0
        with open(input_path) as input_file:
            for row in csv.DictReader(input_file, delimiter="\t"):
                if abs(float(row['seg.mean'])) >= constants.MINIMUM_MAGNITUDE_SEG_MEAN:
                    total += int(row['loc.end']) - int(row['loc.start'])
        # TODO see GCGI-347 for possible updates to genome size
        fga = float(total)/constants.GENOME_SIZE
        return fga

def read_pan_cancer_percentile(genomic_landscape_plugin, data_dir, tmb):
        tmb_array = []
        with open(os.path.join(data_dir, constants.TMBCOMP_TCGA)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                tmb_array.append(float(row[constants.TMB_HEADER]))
        ecdf = ECDF(tmb_array)
        percentile = ecdf(tmb)*100
        return percentile

def get_tmb_count(genomic_landscape_plugin, work_dir):
        # Count the somatic mutations
        # Splice_Region is *excluded* for TMB, *included* in our mutation tables and counts
        # Splice_Region mutations are of interest to us, but excluded from the standard TMB definition
        # The TMB mutation count is (independently) implemented and used in vaf_plot.R
        # See JIRA ticket GCGI-496
        total = 0
        excluded = 0
        with open(os.path.join(work_dir, constants.MUTATIONS_EXTENDED)) as data_file:
            for row in csv.DictReader(data_file, delimiter="\t"):
                total += 1
                if row.get(constants.VARIANT_CLASSIFICATION) in constants.TMB_EXCLUDED:
                    excluded += 1
        tmb_count = total - excluded
        msg = "Found {} small mutations and indels, of which {} are counted for TMB".format(total,
                                                                                            tmb_count)
        genomic_landscape_plugin.logger.debug(msg)
        return tmb_count


def write_biomarker_plot(genomic_landscape_plugin, work_dir, r_script_dir, tcga_code, marker, tmb):
      out_path = os.path.join(work_dir, marker+'.svg')
      args = [
          os.path.join(r_script_dir, 'tmb_plot.R'),
          '-d', work_dir,
          '-c', tcga_code,
          '-m', marker,
          '-t', str(tmb)
      ]
      subprocess_runner(genomic_landscape_plugin.log_level, genomic_landscape_plugin.log_path).run(args)
      genomic_landscape_plugin.logger.info("Wrote tmb plot to {0}".format(out_path))
      return out_path
