"""Assay names/descriptions for use by multiple plugins"""

# assay name constants, can be imported by plugins if needed
WGTS = 'WGTS'
WGS = 'WGS'
WGTS40X = 'WGTS40X'
TAR = 'TAR'
PWGS = 'PWGS'

ASSAY_LOOKUP = {
    # WGTS/WGS default to 80X
    'WGTS': 'Whole genome and transcriptome sequencing (WGTS)'+\
    '-80X Tumour, 30X Normal (v5.0)',
    'WGS': 'Whole genome sequencing (WGS)-80X Tumour, 30X Normal (v5.0)',
    # WGTS/WGS at 40X - seldom done now, but included for completeness
    'WGTS40X': 'Whole genome and transcriptome sequencing (WGTS)'+\
    '-40X Tumour, 30X Normal (v5.0)',
    'WGS40X': 'Whole genome sequencing (WGS)-40X Tumour, 30X Normal (v5.0)',
    # other
    'TAR': 'Targeted Sequencing - REVOLVE Panel - cfDNA and Buffy Coat (v3.0)',
    'PWGS': 'Plasma Whole Genome Sequencing (v3.0)'
}

def get_description(name):
    return ASSAY_LOOKUP.get(name)

def name_status(name):    
    """Convenience method to get name validity and error message (if any)"""
    if name in ASSAY_LOOKUP:
        ok = True
        msg = None
    else:
        ok = False
        keys = sorted(list(ASSAY_LOOKUP.keys()))
        msg = "Assay name {0} not in permitted lookup values {1}".format(name, keys)
    return [ok, msg]
