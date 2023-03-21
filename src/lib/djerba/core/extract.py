"""Class to extract core data elements from INI parameters"""

import logging
from djerba.util.logger import logger

class extractor(logger):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)

    def run(self, config):
        # TODO validate config is complete
        # populate additional data fields
        data = {
            'core': {
                "assay_type": "WGTS",
                "author": "Test Author",
                "oicr_logo": 'OICR logo goes here',
                "patient_info": {
                    "Assay": "Whole genome and transcriptome sequencing (WGTS)-80X Tumour, 30X Normal (v2.0)",
                    "Blood Sample ID": "PLACEHOLDER",
                    "Patient Genetic Sex": "Male",
                    "Patient LIMS ID": "PLACEHOLDER",
                    "Patient Study ID": "PLACEHOLDER",
                    "Primary cancer": "Pancreatic Adenocarcinoma",
                    "Report ID": "PLACEHOLDER",
                    "Requisition ID": "REQ01",
                    "Requisition Approved": "2021/01/01",
	            "Requisition ID": "REQ01",
                    "Site of biopsy/surgery": "PLACEHOLDER",
                    "Study": "PLACEHOLDER",
                    "Project": "PLACEHOLDER",
                    "Tumour Sample ID": "PLACEHOLDER"
                },
                "sample_info_and_quality": {
                    "Callability (%)": 90.0,
                    "Coverage (mean)": 120.0,
                    "Estimated Ploidy": 3.0,
                    "Estimated Cancer Cell Content (%)": 90.0,
                    "OncoTree code": "PAAD",
                    "Sample Type": "LCM"
                },
                "genomic_summary": "Placeholder for testing",
                "technical_notes": "No technical notes supplied.",
                "failed": False,
                "pipeline_version": "1.0",
                "purity_failure": False,
                "report_date": None,
                "djerba_version": "PLACEHOLDER",
            },
            'plugins': {},
        }
        for key in ['trinity', 'neo']:
            data[key] = config['core'][key]
        return data
