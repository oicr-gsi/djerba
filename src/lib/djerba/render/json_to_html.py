"""collection of functions for rendering Djerba content in Mako"""

import djerba.render.constants as constants
import re
import sys
from time import strftime

class html_builder:

    TR_START = '<tr style="text-align:left;">'
    TR_END = '</tr>'

    def __init__(self, purity_failure=False):
        # if purity_failure = True, do custom formatting of purity value
        self.purity_failure = purity_failure

    def _href(self, url, text):
        return '<a href="{0}">{1}</a>'.format(url, text)

    def _td(self, content, italic=False, width=None):
        # make a <td> table entry with optional attributes
        attrs = []
        if italic:
            attrs.append('style="font-style: italic;"')
        if width:
            attrs.append('width="{0}%"'.format(width))
        if len(attrs) > 0:
            td = '<td {0}>{1}</td>'.format(' '.join(attrs), content)
        else:
            td = '<td>{0}</td>'.format(content)
        return td

    def genomic_landscape_table_rows(self, genomic_landscape_args):
        widths = [55,45]
        key_groups = [
            [constants.TMB_TOTAL, constants.PERCENT_GENOME_ALTERED],
            [constants.CANCER_SPECIFIC_PERCENTILE, constants.CANCER_SPECIFIC_COHORT],
            [constants.PAN_CANCER_PERCENTILE, constants.PAN_CANCER_COHORT],
        ]
        return self.key_value_table_rows(genomic_landscape_args, key_groups, widths)

    def key_value_table_rows(self, args, key_groups, widths):
        """Make a table to show key/value fields, with varying column widths"""
        flattened = [k for group in key_groups for k in group]
        values = {}
        for key in flattened:
            if key in constants.PATIENT_INFO_CONSTANT_FIELDS:
                value = constants.PATIENT_INFO_CONSTANT_FIELDS.get(key)
            elif key == constants.DATE_OF_REPORT:
                value = strftime("%Y/%m/%d")
            elif key == constants.TMB_TOTAL:
                tmb_total = args[constants.TMB_TOTAL]
                tmb_per_mb = args[constants.TMB_PER_MB]
                value = "{0} mutations. {1} coding mutations per Mb".format(tmb_total, tmb_per_mb)
            else:
                value = args.get(key)
            values[key] = value
        rows = []
        for key_group in key_groups:
            row_items = ['<tr>']
            total = len(key_group)
            for i in range(total):
                width = widths[i]
                key = key_group[i]
                value = values[key]
                if key == constants.PURITY_PERCENT and self.purity_failure:
                    template = '<td width="{0}%" style="color:red;"><strong>{1}:</strong> {2}</td>'
                else:
                    template = '<td width="{0}%"><strong>{1}:</strong> {2}</td>'
                cell = template.format(width, key, value)
                row_items.append(cell)
            row_items.append('</tr>')
            rows.append("\n".join(row_items))
        return rows

    def oncogenic_CNVs_header(self):
        names = [
            constants.GENE,
            constants.CHROMOSOME,
            constants.ALTERATION,
            constants.ONCOKB
        ]
        return self.table_header(names)

    def oncogenic_CNVs_rows(self, mutation_info):
        row_fields = mutation_info[constants.BODY]
        rows = []
        for row in row_fields:
            cells = [
                self._td(self._href(row[constants.GENE_URL], row[constants.GENE]), italic=True),
                self._td(row[constants.CHROMOSOME]),
                self._td(row[constants.ALTERATION]),
                self._td(row[constants.ONCOKB]),
            ]
            rows.append(self.table_row(cells))
        return rows

    def oncogenic_small_mutations_and_indels_header(self):
        names = [
            constants.GENE,
            constants.CHROMOSOME,
            constants.PROTEIN,
            constants.MUTATION_TYPE,
            constants.VAF_PERCENT,
            constants.DEPTH,
            constants.COPY_STATE,
            constants.ONCOKB
        ]
        return self.table_header(names)

    def oncogenic_small_mutations_and_indels_rows(self, mutation_info):
        row_fields = mutation_info[constants.BODY]
        rows = []
        for row in row_fields:
            depth = "{0}/{1}".format(row[constants.TUMOUR_ALT_COUNT], row[constants.TUMOUR_DEPTH])
            cells = [
                self._td(self._href(row[constants.GENE_URL], row[constants.GENE]), italic=True),
                self._td(row[constants.CHROMOSOME]),
                self._td(self._href(row[constants.PROTEIN_URL], row[constants.PROTEIN])),
                self._td(row[constants.MUTATION_TYPE]),
                self._td(row[constants.VAF_PERCENT]),
                self._td(depth),
                self._td(row[constants.COPY_STATE]),
                self._td(row[constants.ONCOKB])
            ]
            rows.append(self.table_row(cells))
        return rows
    
    def patient_table_rows_2_cols(self, patient_args):
        """Get the patient info table: After initial header, before Sample Information & Quality"""
        widths = [63, 37]
        key_groups = [
            [constants.HOSPITAL, constants.REQUISITIONER_EMAIL],
            [constants.PRIMARY_CANCER, constants.SITE_OF_BIOPSY_OR_SURGERY],
            [constants.TUMOUR_SAMPLE_ID, constants.BLOOD_SAMPLE_ID],
        ]
        return self.key_value_table_rows(patient_args, key_groups, widths)
    
    def patient_table_rows_3_cols(self, patient_args):
        """Get the patient info table: After initial header, before Sample Information & Quality"""
        widths = [35, 28, 37]
        key_groups = [
            [constants.DATE_OF_REPORT, constants.REQ_APPROVED_DATE, constants.REPORT_ID],
            [constants.STUDY, constants.PATIENT_STUDY_ID, constants.PATIENT_LIMS_ID],
            [constants.NAME, constants.DOB, constants.SEX],
            [constants.PHYSICIAN, constants.LICENCE_NUMBER, constants.PHONE_NUMBER],
        ]
        return self.key_value_table_rows(patient_args, key_groups, widths)

    def sample_information_and_quality_rows(self, sample_args):
        widths = [34, 33, 33]
        key_groups = [
            [constants.ONCOTREE_CODE, constants.CALLABILITY_PERCENT, constants.COVERAGE_MEAN],
            [constants.SAMPLE_TYPE, constants.PURITY_PERCENT, constants.PLOIDY],
        ]
        return self.key_value_table_rows(sample_args, key_groups, widths)

    def structural_variants_and_fusions_header(self):
        names = [
            constants.GENE,
            constants.CHROMOSOME,
            constants.FUSION,
            constants.FRAME,
            constants.MUTATION_EFFECT,
            constants.ONCOKB
        ]
        return self.table_header(names)

    def structural_variants_and_fusions_rows(self, mutation_info):
        row_fields = mutation_info[constants.BODY]
        rows = []
        for row in row_fields:
            if re.search('intragenic', row[constants.FUSION]): # omit intragenic fusions
                continue
            cells = [
                self._td(self._href(row[constants.GENE_URL], row[constants.GENE]), italic=True),
                self._td(row[constants.CHROMOSOME]),
                self._td(row[constants.FUSION]),
                self._td(row[constants.FRAME]),
                self._td(row[constants.MUTATION_EFFECT]),
                self._td(row[constants.ONCOKB])
            ]
            rows.append(self.table_row(cells))
        return rows

    def supplementary_info_header(self):
        names = [
            constants.GENE,
            constants.CHROMOSOME,
            constants.SUMMARY
        ]
        return self.table_header(names)

    def supplementary_info_rows(self, row_fields):
        rows = []
        for row in row_fields:
            # italicize the gene name where it appears in the summary
            summary = re.sub('(^| ){0}[,.;: ]'.format(row[constants.GENE]),
                             lambda m: '<i>{0}</i>'.format(m[0]),
                             row[constants.SUMMARY])
            cells = [
                self._td(self._href(row[constants.GENE_URL], row[constants.GENE]), italic=True),
                self._td(row[constants.CHROMOSOME]),
                self._td(summary)
            ]
            rows.append(self.table_row(cells))
        return rows

    def table_header(self, names):
        items = ['<thead style="background-color:white">', '<tr>']
        for name in names:
            items.extend(['<th style="text-align:left;">', name, '</th>'])
        items.extend(['</tr>', '</thead>'])
        return ''.join(items)

    def table_row(self, cells):
        items = [self.TR_START, ]
        items.extend(cells)
        items.append(self.TR_END)
        return ''.join(items)

    def therapies_header(self):
        return self.table_header(['Gene(s)', 'Alteration', 'Treatment(s)', 'OncoKB'])

    def therapies_table_rows(self, row_fields):
        rows = []
        for row in row_fields:
            widths = iter([15, 15, 55, 15])
            # may have a pair of genes (fusions) or single gene (otherwise)
            gene_urls = row[constants.GENES_AND_URLS]
            gene_links = [self._href(gene_urls[gene], gene) for gene in sorted(list(gene_urls.keys()))]
            cells = [
                self._td(', '.join(gene_links), True, next(widths)),
                self._td(self._href(row[constants.ALT_URL], row[constants.ALT]), False, next(widths)),
                self._td(row[constants.TREATMENT], False, next(widths)),
                self._td(row[constants.ONCOKB], False, next(widths)),
            ]
            rows.append(self.table_row(cells))
        return rows
