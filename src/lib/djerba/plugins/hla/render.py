from djerba.util.html import html_builder as hb
class html_builder:

    # Header constants
    GENE_NAME = 'Gene Name'
    ZYGOSITY = 'Zygosity'
    ALLELE = 'Allele'
    ABUNDANCE = 'Abundance'
    QUALITY = 'Quality'

    # Extract constants
    _GENE_NAME = 'Gene name'
    _ZYGOSITY = 'Zygosity'
    _ALLELE = 'Allele'
    _ABUNDANCE = 'Abundance'
    _QUALITY = 'Quality'
    _BODY = 'Body'

    def hla_header(self):
        """
        Creates the header for the HLA analysis table.
        """
        names = [
            self.GENE_NAME,
            self.ZYGOSITY,
            self.ALLELE,
            self.ABUNDANCE,
            self.QUALITY
        ]
        return hb.thead(names)

    def hla_rows(self, hla_data):
        """
        Creates the rows for the HLA analysis table.
        """
        row_fields = hla_data[self._BODY]
        rows = []
        for row in row_fields:
            cells = [
                hb.td(row[self._GENE_NAME]),
                hb.td(row[self._ZYGOSITY]),
                hb.td(row[self._ALLELE]),
                hb.td(row[self._ABUNDANCE]),
                hb.td(row[self._QUALITY]),
            ]
            rows.append(hb.table_row(cells))
        return rows

