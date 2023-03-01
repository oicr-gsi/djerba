"""collection of functions for rendering Djerba content in Mako"""

import djerba.render.constants as constants
import re
from markdown import markdown
from time import strftime
from string import Template
from djerba.util.image_to_base64 import converter

class html_builder:

    TR_START = '<tr style="text-align:left;">'
    TR_END = '</tr>'
    EXPR_COL_INDEX_SMALL_MUT = 6 # position of expression column (if any) in small mutations table
    EXPR_COL_INDEX_CNV = 2 # position of expression column (if any) in cnv table
    EXPR_SHORT_NAME = 'Expr. (%)'

    def __init__(self, purity_failure=False):
        # if purity_failure = True, do custom formatting of purity value
        self.purity_failure = purity_failure
        self.bar_maker = display_bar_maker(0,100)

    def _expression_display(self, expr):
        if expr==None:
            return 'NA'
        else:
            return self.bar_maker.get_bar_element(round(expr*100))

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

    def _td_oncokb(self, level):
        # make a table cell with an OncoKB level symbol
        # permitted levels must have a format defined in style.css
        onc = 'Oncogenic'
        l_onc = 'Likely Oncogenic'
        p_onc = 'Predicted Oncogenic'
        level = re.sub('Level ', '', level) # strip off 'Level ' prefix, if any
        permitted_levels = ['1', '2', '3A', '3B', '4', 'R1', 'R2', onc, l_onc, p_onc]
        if not level in permitted_levels:
            msg = "Input '{0}' is not a permitted OncoKB level".format(level)
            raise RuntimeError(msg)
        if level in [onc, l_onc, p_onc]:
            shape = 'square'
        else:
            shape = 'circle'
        if level == onc:
            level = 'N1'
        elif level == l_onc:
            level = 'N2'
        elif level == p_onc:
            level = 'N3'
        div = '<div class="{0} oncokb-level{1}">{2}</div>'.format(shape, level, level)
        return self._td(div)

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

    def markdown_to_html(self, markdown_string):
        return markdown(markdown_string)

    def oncogenic_CNVs_header(self, mutation_info):
        names = [
            constants.GENE,
            constants.CHROMOSOME,
            constants.ALTERATION,
            constants.ONCOKB
        ]
        if mutation_info[constants.HAS_EXPRESSION_DATA]:
            names.insert(self.EXPR_COL_INDEX_CNV, self.EXPR_SHORT_NAME)
        return self.table_header(names)

    def oncogenic_CNVs_rows(self, mutation_info):
        row_fields = mutation_info[constants.BODY]
        rows = []
        for row in row_fields:
            cells = [
                self._td(self._href(row[constants.GENE_URL], row[constants.GENE]), italic=True),
                self._td(row[constants.CHROMOSOME]),
                self._td(row[constants.ALTERATION]),
                self._td_oncokb(row[constants.ONCOKB]),
            ]
            if mutation_info[constants.HAS_EXPRESSION_DATA]:
                metric = self._expression_display(row[constants.EXPRESSION_METRIC])
                cells.insert(self.EXPR_COL_INDEX_CNV, self._td(metric))
            rows.append(self.table_row(cells))
        return rows

    def oncogenic_small_mutations_and_indels_header(self, mutation_info):
        names = [
            constants.GENE,
            'Chr.',
            constants.PROTEIN,
            constants.MUTATION_TYPE,
            constants.VAF_NOPERCENT,
            constants.DEPTH,
            constants.COPY_STATE,
            constants.ONCOKB
        ]
        if mutation_info[constants.HAS_EXPRESSION_DATA]:
            names.insert(self.EXPR_COL_INDEX_SMALL_MUT, self.EXPR_SHORT_NAME)
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
                self._td_oncokb(row[constants.ONCOKB])
            ]
            if mutation_info[constants.HAS_EXPRESSION_DATA]:
                metric = self._expression_display(row[constants.EXPRESSION_METRIC])
                cells.insert(self.EXPR_COL_INDEX_SMALL_MUT, self._td(metric))
            rows.append(self.table_row(cells))
        return rows

    def patient_table_report_cols(self, patient_args):
        """Get the patient info table: After initial header, before Sample Information & Quality"""
        widths = [[17,20], [19,35]]
        key_groups = [
            [constants.PATIENT_LIMS_ID, constants.TUMOUR_SAMPLE_ID],
            [constants.PATIENT_STUDY_ID, constants.BLOOD_SAMPLE_ID],
            [constants.STUDY , constants.REPORT_ID]
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
        widths = [[30,5], [15,25]]
        key_groups = [
            [constants.ONCOTREE_CODE, constants.SAMPLE_TYPE],
            [constants.CALLABILITY_PERCENT, constants.COVERAGE_MEAN],
            [constants.PURITY_PERCENT, constants.PLOIDY]
        ]
        return self.key_value_table_rows(sample_args, key_groups, widths)

    def section_cells_begin(self, section_title, main_or_supp):
        # begin a cell structure with title in left-hand cell, body in right-hand cell
        permitted = ['main', 'supp']
        if main_or_supp not in permitted:
            msg = "Section type argument '{0}' not in {1}".format(main_or_supp, permitted)
            self.logger.error(msg)
            raise RuntimeError(msg)
        template = '<hr class="big-white-line" ><div class="twocell{0}"><div class="oneoftwocell{0}">{1}</div><div class="twooftwocell{0}" ><hr class="big-line" >'
        cell = template.format(main_or_supp,section_title)
        return cell

    def section_cells_end(self):
        # closes <div class="twocell... and <div class="twooftwocell...
        return "</div></div>\n"

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

class display_bar_maker:

    """
    Make a SVG display with a coloured dot on a horizontal bar
    Intended to represent a quantity in a table cell
    """

    BAR_OFFSET = 4  # offset of bar from left-hand border
    BAR_LENGTH = 30 # length of display bar, in pixels

    TEMPLATE = '<svg width="67" height="12"><text x="39" y="11" text-anchor="start" '+\
                'font-size="12" fill=${text_colour}>${value}</text><g><line x1="${bar_start}" '+\
                'y1="8" x2="${bar_end}" y2="8" style="stroke: gray; '+\
                'stroke-width: 2px;"></line><circle cx="${pos}" cy="8" r="3" '+\
                'fill="${circle_colour}"></circle></g></svg>'

    COLOUR_LOW = 'blue'
    COLOUR_HIGH = 'red'

    def __init__(self, min_val, max_val, blue_max=0.2, red_min=0.8):
        self.min_val = min_val
        self.max_val = max_val
        self.x_range = float(max_val - min_val)
        if self.x_range <= 0:
            raise RuntimeError("Invalid range: min={0}, max={1}".format(min_val, max_val))
        self.blue_max = blue_max
        self.red_min = red_min

    def get_circle_colour(self, x):
        if x <= self.blue_max:
            return self.COLOUR_LOW
        elif x >= self.red_min:
            return self.COLOUR_HIGH
        else:
            return 'gray'

    def get_text_colour(self, x):
        if x <= self.blue_max:
            return self.COLOUR_LOW
        elif x >= self.red_min:
            return self.COLOUR_HIGH
        else:
            return 'black'

    def get_circle_position(self, x):
        return x*self.BAR_LENGTH + self.BAR_OFFSET

    def get_bar_element(self, x):
        x_raw = x
        x = x / self.x_range
        if x < 0 or x > 1:
            raise ValueError("Input {0} out of range ({1}, {2})".format(x, self.min_val, self.max_val))
        params = {
            'value': x_raw,
            'bar_start': self.BAR_OFFSET,
            'bar_end': self.BAR_LENGTH+self.BAR_OFFSET,
            'pos': self.get_circle_position(x),
            'circle_colour': self.get_circle_colour(x),
            'text_colour': self.get_text_colour(x)
        }
        return Template(self.TEMPLATE).substitute(params)
