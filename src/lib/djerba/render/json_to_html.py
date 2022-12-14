"""collection of functions for rendering Djerba content in Mako"""

import djerba.render.constants as constants
import re
from markdown import markdown
from time import strftime
from djerba.util.image_to_base64 import converter

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


    def assemble_biomarker_plot(self,biomarker,plot):
        template='<img id="{0}" style="width: 100%; " src="{1}"'
        cell = template.format(biomarker,plot)
        return(cell)

    def biomarker_table_rows(self, genomic_biomarker_args):
        row_fields = genomic_biomarker_args[constants.BODY]
        rows = []
        for row in row_fields:
            if row[constants.ALT] == "TMB":
                continue
            else:
                cells = [
                    self._td(row[constants.ALT]),
                    self._td(row[constants.METRIC_CALL]),
                    self._td(self.assemble_biomarker_plot(row[constants.ALT],row[constants.METRIC_PLOT]))
                ]
                rows.append(self.table_row(cells))
        return rows

    def k_comma_format(self,value):
        value_formatted = f'{value:,}'
        return(value_formatted)

    def key_value_table_rows(self, args, key_groups, widths):
        """Make a table to show key/value fields, with varying column widths"""
        flattened = [k for group in key_groups for k in group]
        values = {}
        for key in flattened:
            # special cases
            # strings such as "Unknown" are permissible for purity/ploidy/coverage/callability
            if key in constants.PATIENT_INFO_CONSTANT_FIELDS:
                value = constants.PATIENT_INFO_CONSTANT_FIELDS.get(key)
            elif key == constants.DATE_OF_REPORT:
                value = strftime("%Y/%m/%d")
            elif key == constants.TMB_TOTAL:
                tmb_total = args[constants.TMB_TOTAL]
                tmb_per_mb = args[constants.TMB_PER_MB]
                value = "{0} mutations. {1} coding mutations per Mb".format(tmb_total, tmb_per_mb)
            elif key in [constants.PLOIDY, constants.COVERAGE_MEAN, constants.CALLABILITY_PERCENT] \
                 and (isinstance(args[key], float) or isinstance(args[key], int)):
                value = "{:0.1f}".format(args[key])
            elif key == constants.PURITY_PERCENT and (isinstance(args[key], float) or isinstance(args[key], int)):
                value = str(int(round(args[key], 0)))
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
                    template = '<td width="{0}%" style="color:red;">{1}:</td><td width="{2}%">{3}</td>'
                else:
                    template = '<td width="{0}%">{1}:</td><td width="{2}%" >{3}</td>'
                cell = template.format(width[0], key, width[1], value)
                row_items.append(cell)
            row_items.append('</tr>')
            rows.append("\n".join(row_items))
        return rows

    def make_ordinal(self,n):
        '''
        Convert an integer into its ordinal representation::

            make_ordinal(0)   => '0th'
            make_ordinal(3)   => '3rd'
            make_ordinal(122) => '122nd'
            make_ordinal(213) => '213th'
        '''
        n = int(n)
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return str(n) + suffix

    def make_sections_into_cells(self,section_title,main_or_supp):
        template = '<hr class="big-white-line" ><div class="twocell{0}"><div class="oneoftwocell{0}">{1}</div><div class="twooftwocell{0}" ><hr class="big-line" >'  
        cell = template.format(main_or_supp,section_title)
        return cell

    def markdown_to_html(self, markdown_string):
        return markdown(markdown_string)

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
            constants.VAF_NOPERCENT,
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
    
    def patient_table_report_cols(self, patient_args):
        """Get the patient info table: After initial header, before Sample Information & Quality"""
        widths = [[25,25], [25,25]]
        key_groups = [
            [constants.REPORT_ID, constants.PATIENT_LIMS_ID],
            [constants.BLOOD_SAMPLE_ID, constants.PATIENT_STUDY_ID],
            [constants.TUMOUR_SAMPLE_ID , constants.STUDY]
        ]
        return self.key_value_table_rows(patient_args, key_groups, widths)
    
    def patient_table_id_cols(self, patient_args):
        """Get the patient info table: After initial header, before Sample Information & Quality"""
        widths = [[25,15],[23,38]]
        key_groups = [
            [constants.DATE_OF_REPORT , constants.REQUISITIONER_EMAIL],
            [constants.REQ_APPROVED_DATE, constants.NAME],
            [constants.SEX, constants.DOB],
            [constants.LICENCE_NUMBER, constants.PHYSICIAN],
            [constants.PHONE_NUMBER, constants.HOSPITAL]
        ]
        return self.key_value_table_rows(patient_args, key_groups, widths)

    def process_oncokb_colours(self,oncokb_level):
        template = '<div  class="circle oncokb-level{0}">{0}</div>'  
        split_oncokb = oncokb_level.split(" ",2)
        oncokb_circle = template.format(split_oncokb[1])
        return(oncokb_circle)
        
    def pull_biomarker_text(self, genomic_biomarker_args, biomarker):
        row_fields = genomic_biomarker_args[constants.BODY]
        for row in row_fields:
            if row[constants.ALT] == biomarker:
                metric_text = row[constants.METRIC_TEXT]
        return metric_text

    def sample_information_and_quality_rows(self, sample_args):
        widths = [[35,15], [20,15]]
        key_groups = [
            [constants.ONCOTREE_CODE, constants.SAMPLE_TYPE],
            [constants.CALLABILITY_PERCENT, constants.COVERAGE_MEAN],
            [constants.PURITY_PERCENT, constants.PLOIDY]
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

    def supplementary_gene_info_header(self):
        names = [
            constants.GENE,
            constants.SUMMARY
        ]
        return self.table_header(names)

    def supplementary_gene_info_rows(self, row_fields):
        rows = []
        for row in row_fields:
            # italicize the gene name where it appears in the summary
            # name must be:
            # - preceded by a space or start-of-string
            # - followed by a space or listed punctuation
            summary = re.sub('(^| ){0}[,.;: ]'.format(row[constants.GENE]),
                             lambda m: '<i>{0}</i>'.format(m[0]),
                             row[constants.SUMMARY])
            cells = [
                self._td(self._href(row[constants.GENE_URL], row[constants.GENE]), italic=True),
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
        return self.table_header(['OncoKB', 'Treatment(s)','Gene(s)', 'Alteration' ])

    def therapies_table_rows(self, row_fields):
        rows = []
        for row in row_fields:
            widths = iter([1, 59, 20, 20])
            # may have a pair of genes (fusions) or single gene (otherwise)
            gene_urls = row[constants.GENES_AND_URLS]
            gene_links = [self._href(gene_urls[gene], gene) for gene in sorted(list(gene_urls.keys()))]
            cells = [
                self._td(self.process_oncokb_colours(row[constants.ONCOKB]), False, next(widths)),
                self._td(row[constants.TREATMENT], False, next(widths)),
                self._td(', '.join(gene_links), True, next(widths)),
                self._td(self._href(row[constants.ALT_URL], row[constants.ALT]), False, next(widths)),
            ]
            rows.append(self.table_row(cells))
        return rows

