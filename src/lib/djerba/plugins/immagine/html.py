"""Methods to generate immagine table similar to snv indel table in html"""

import djerba.core.constants as core_constants
import djerba.plugins.immagine.constants as constants
from djerba.util.html import html_builder as hb

class immagine_table_builder:

    EXPR_COL_TITLE = 'Expr. (%)'
    LOH_COL_TITLE = 'LOH'
    CATEGORIES = [
        {
            "name": "Hallmark Cancer Genes",
            "colour": "#ffffff",
            "genes": [
                "TP53", "MYC", "NRAS", "KRAS", "CDKN2C",
                "NFKB1", "NFKB2", "RB1", "BRAF", "CDK6", "ATM"
            ]
        },
        {
            "name": "Myeloma Associated Genes",
            "colour": "#ffffff",
            "genes": [
                "TNFRSF17", "CD38", "CRBN", "FCRH5", "FGFR3", "GPRC5D", "CKS1B"
            ]
        }
    ]


    @classmethod
    def make_header(klass, results):
        names = [
            'Categories',
            'Gene',
            'Mutation Alteration',
            'Mutation Type',
            'Copy Number'
        ]
        if results[constants.HAS_EXPRESSION_DATA]:
            names.insert(len(names), klass.EXPR_COL_TITLE)
        return hb.thead(names)


    @classmethod
    def make_rows(klass, results):
        rows = []

        for category in klass.CATEGORIES: # Hallmark Cancer Genes, then Myeloma Associated Genes
            for i, gene in enumerate(category["genes"]): # make a row for every gene in each category

                result = results.get(gene, {})
                cells = []

                if i == 0: # first column is just either category name 
                    cells.append(
                        hb.td_kwargs(category["name"], rowspan=len(category["genes"]))
                    )

                cells.extend([
                    hb.td_kwargs(gene, italic=True),
                    hb.td_kwargs(result.get(constants.MUTATION_ALT, "")),
                    hb.td_kwargs(result.get(constants.MUTATION_TYPE, "")),
                    hb.td_kwargs(result.get(constants.COPY_NUMBER, "")),
                    #hb.td(result.get(constants.EXPRESSION_PERCENTILE, "NA"))
                ])

                if results[constants.HAS_EXPRESSION_DATA]:
                    metric = result.get(constants.EXPRESSION_PERCENTILE, "NA")
                    if metric != "NA":
                        metric_cell = hb.td_kwargs(hb.expression_display(metric))
                    else:
                        metric_cell = hb.td_kwargs(metric)
                    cells.insert(len(cells), metric_cell)

                rows.append(
                    hb.tr_kwargs(
                        cells,
                        #style=f"background-color: {category['colour']};"
                    )
                )
        return rows

    @classmethod
    def get_apobec_sentence(klass, results):
        """
        Writes the sentence at the end of the APOBEC Gene Signature table.
        """
        present = [sig for sig, detected in results.get(constants.APOBEC_SIGS).items() if detected]
        if not present:
            return "The tumour does not demonstrate evidence of APOBEC-associated mutagenesis (SBS2 or SBS13)."
        return f"The tumour demonstrates evidence of APOBEC-associated mutagenesis ({' and '.join(present)})."

    @classmethod
    def get_high_risk_sentence(klass, results):
        """
        Writes the sentence at the end of the APOBEC Gene Signature table.
        """
        present = results.get(constants.HIGH_RISK)
        if present:
            return "This patient fits the criteria for high-risk myeloma as defined by the IMWG."
        else:
            return "This patient does not fit the criteria for high-risk myeloma as defined by the IMWG."

