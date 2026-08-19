"""
TAR germline plugin.

Reports germline variants called with EfficientDV and annotated with VEP,
restricted to the Hereditary Cancer Comprehensive Panel and annotated with
OncoKB for oncogenicity. See JIRA GCGI-1765, GCGI-1763, GBS-7157.
"""

import csv
import logging
import os

import djerba.core.constants as core_constants
import djerba.plugins.tar.germline.constants as gc
import djerba.util.oncokb.constants as oncokb_constants
from djerba.mergers.gene_information_merger.factory import factory as gim_factory
from djerba.mergers.treatment_options_merger.factory import factory as tom_factory
from djerba.plugins.base import plugin_base
from djerba.plugins.tar.germline.extract import data_builder
from djerba.plugins.tar.germline.preprocess import preprocess
from djerba.util.html import html_builder as hb
from djerba.util.oncokb.tools import gene_summary_reader
from djerba.util.oncokb.tools import levels as oncokb_levels
from djerba.util.render_mako import mako_renderer


class main(plugin_base):

    # Renders between tar.snv_indel (600) and tar.swgs (700), so both small-variant sections are adjacent.
    PRIORITY = 650
    PLUGIN_VERSION = '1.0.0'
    TEMPLATE_NAME = 'html/germline_template.html'

    def specify_params(self):
        # Germline MAF is supplied manually for now.
        self.add_ini_required(gc.GERMLINE_MAF_FILE)
        for key in [gc.DONOR, gc.ONCOTREE, gc.TUMOUR_ID]:
            self.add_ini_discovered(key)

        self.set_ini_default(oncokb_constants.ONCOKB_CACHE,
                             oncokb_constants.DEFAULT_CACHE_PATH)
        self.set_ini_default(oncokb_constants.APPLY_CACHE, False)
        self.set_ini_default(oncokb_constants.UPDATE_CACHE, False)
        self.set_ini_default(core_constants.ATTRIBUTES, 'clinical')
        self.set_priority_defaults(self.PRIORITY)

    def configure(self, config):
        config = self.apply_defaults(config)
        wrapper = self.get_config_wrapper(config)
        input_data = self.workspace.read_maybe_input_params()
        for key in [gc.DONOR, gc.ONCOTREE, gc.TUMOUR_ID]:
            if wrapper.my_param_is_null(key):
                if input_data is not None:
                    wrapper.set_my_param(key, input_data[key])
                else:
                    msg = "Cannot find {0} in manual config " \
                          "or input_params.json".format(key)
                    self.logger.error(msg)
                    raise RuntimeError(msg)
        return wrapper.get_config()

    def extract(self, config):
        wrapper = self.get_config_wrapper(config)
        work_dir = self.workspace.get_work_dir()
        oncotree_code = wrapper.get_my_string(gc.ONCOTREE)
        tumour_id = wrapper.get_my_string(gc.TUMOUR_ID)
        maf_file = wrapper.get_my_string(gc.GERMLINE_MAF_FILE)

        data = self.get_starting_plugin_data(wrapper, self.PLUGIN_VERSION)

        germline_dir = preprocess(
            work_dir, wrapper, tumour_id, maf_file,
            self.log_level, self.log_path
        ).run()

        extractor = data_builder(germline_dir, oncotree_code,
                                 self.log_level, self.log_path)
        reportable, vus = extractor.build_rows()

        # Define all template variables so they render correctly even when values are 0 or empty.
        data['results'] = {
            gc.TOTAL_GERMLINE_VARIANTS: extractor.count_total(),
            gc.REPORTABLE_GERMLINE_VARIANTS: len(reportable),
            gc.VUS_GERMLINE_VARIANTS: len(vus),
            gc.PANEL_GENE_COUNT: len(gc.PANEL_GENES),
            gc.BODY: reportable,
            gc.VUS_BODY: vus,
        }
        data['merge_inputs'] = self.get_merge_inputs(germline_dir,
                                                     oncotree_code)
        return data

    def render(self, data):
        renderer = mako_renderer(self.get_module_dir())
        return renderer.render_name(self.TEMPLATE_NAME, data)

    def get_merge_inputs(self, germline_dir, oncotree_code):
        """
        Gene and therapy entries for the shared report tables.

        Therapy entries carry a '(germline)' tag on the alteration.
        treatment_options_merger deduplicates on (OncoKB level, Alteration,
        Gene) last-wins, so without the tag a germline and somatic hit on the
        same variant would silently collapse into a single row.
        """
        gene_info = []
        treatments = []
        gene_info_factory = gim_factory(self.log_level, self.log_path)
        treatment_option_factory = tom_factory(self.log_level, self.log_path)
        summaries = gene_summary_reader(self.log_level, self.log_path)
        input_path = os.path.join(germline_dir, gc.GERMLINE_ONCOGENIC)
        with open(input_path) as input_file:
            for row_input in csv.DictReader(input_file, delimiter="\t"):
                gene = row_input[gc.HUGO_SYMBOL]
                if gene in ('', 'NA', 'None', 'Unknown'):
                    continue
                level = oncokb_levels.parse_oncokb_level(row_input)
                if level not in ('Unknown', 'NA'):
                    gene_info.append(gene_info_factory.get_json(
                        gene=gene,
                        summary=summaries.get(gene)
                    ))
                therapies = oncokb_levels.parse_actionable_therapies(row_input)
                for level in therapies.keys():
                    alteration = row_input[gc.HGVSP_SHORT]
                    is_splice = 'splice' in \
                        row_input[gc.VARIANT_CLASSIFICATION].lower()
                    if is_splice or not alteration:
                        alteration = 'p.? ({0})'.format(row_input[gc.HGVSC])
                        alteration_url = hb.build_alteration_url(
                            gene, "Truncating%20Mutations", oncotree_code)
                    else:
                        # URL built from the untagged alteration
                        alteration_url = hb.build_alteration_url(
                            gene, alteration, oncotree_code)
                    treatments.append(treatment_option_factory.get_json(
                        tier=oncokb_levels.tier(level),
                        level=level,
                        gene=gene,
                        alteration=alteration + gc.GERMLINE_TAG,
                        alteration_url=alteration_url,
                        treatments=therapies[level]
                    ))
        return {
            'gene_information_merger': gene_info,
            'treatment_options_merger': treatments
        }
