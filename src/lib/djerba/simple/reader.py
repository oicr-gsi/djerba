"""Read input data for Djerba"""

import json

class reader:
    """Parent class for Djerba data readers"""

    GENE_NAME_KEY = "gene"

    def __init__(self):
        pass

    def get_gene_metrics(self):
        # TODO sanitize gene metrics
        # - ensure all metric names are defined in the schema
        # - ensure each gene has the same set of metric names
        # can load the schema as JSON and interrogate to find permitted names
        pass

    def update_genes(self, genes):
        metrics_for_update_by_gene = self.get_gene_metrics() # dictionary, gene name -> metrics
        if len(genes)==0:
            # no previous entries
            genes = metrics_for_update_by_gene.values()
        else:
            # check consistency with previous entries, and update
            # cannot have two conflicting values for same gene and metric
            for gene in genes:
                metrics_for_update = metrics_for_update_by_gene.get(gene.get(self.GENE_NAME_KEY))
                for key in metrics_for_update.keys():
                    if gene.has_key(key):
                        if gene[key] != metrics_for_update[key]:
                            raise ValueError("Oh, no! Inconsistent metric values")
                    else:
                        genes[key] = metrics_for_update[key]
        return genes
                
    def update_sample(self, info):
        pass
    

class reader_factory:
    """Given the config, construct a reader of the appropriate subclass"""

    GENE_METRICS_KEY = "gene_metrics"
    READER_CLASS_KEY = "reader_class"

    def __init__(self):
        pass

    def create_instance(self, config):
        """
        Return an instance of the reader class named in the config
        Config is a dictionary with a reader_class name, plus other parameters as needed
        """
        classname = config.get(self.READER_CLASS_KEY)
        if classname == None:
            msg = "Unknown or missing %s value in config. " % self.READER_CLASS_KEY
            #self.logger.error(msg)
            raise ValueError(msg)
        klass = globals().get(classname)
        #self.logger.debug("Created instance of %s" % classname)
        return klass(config)

class json_reader(reader):
    """
    Reader for JSON data.
    Supply input as JSON, as default/fallback if other sources not available
    """

    def __init__(self, config):
        self.genes = config.get(self.GENE_METRICS_KEY)
        
