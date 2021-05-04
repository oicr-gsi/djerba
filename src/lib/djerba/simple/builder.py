"""Build CGI report JSON for Djerba"""

from reader import reader_factory

class builder:

    GENE_METRICS_KEY = 'gene_metrics'
    SAMPLE_INFO_KEY = 'sample_info'
    
    def __init__(self, config):
        """config is a JSON data structure: List of objects to configure readers"""
        self.readers = []
        factory = reader_factory()
        for config_item in config:
            self.readers.append(factory.create_instance(config_item))

    def build(self):
        """Build the CGI report JSON structure"""
        pass

    def build_gene_metrics(self):
        """Build the gene metrics array"""
        genes = []
        for reader in self.readers:
            genes = reader.update_genes(genes)
        return genes

    def build_sample_info(self):
        """Build the sample info dictionary"""
        info = {}
        for reader in self.readers:
            info = reader.update_sample(info)
        return info
