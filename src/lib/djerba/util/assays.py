"""Assay names/descriptions for use by multiple plugins"""

import djerba.util.constants as constants

# assay name constants, can be imported by plugins if needed
WGTS = 'WGTS'
WGS = 'WGS'
WGTS40X = 'WGTS40X'
TAR = 'TAR'
PWGS = 'PWGS'

WGTS_SUFFIX = '(v{0})'.format(constants.WGTS_ASSAY_VERSION)
TAR_SUFFIX = '(v{0})'.format(constants.TAR_ASSAY_VERSION)
PWGS_SUFFIX = '(v{0})'.format(constants.PWGS_ASSAY_VERSION)

ASSAY_LOOKUP = {
    # WGTS/WGS default to 80X
    'WGTS': 'Whole genome and transcriptome sequencing (WGTS)'+\
    '-80X Tumour, 30X Normal '+WGTS_SUFFIX,
    'WGS': 'Whole genome sequencing (WGS)-80X Tumour, 30X Normal '+WGTS_SUFFIX,
    # WGTS/WGS at 40X - seldom done now, but included for completeness
    'WGTS40X': 'Whole genome and transcriptome sequencing (WGTS)'+\
    '-40X Tumour, 30X Normal '+WGTS_SUFFIX,
    'WGS40X': 'Whole genome sequencing (WGS)-40X Tumour, 30X Normal '+WGTS_SUFFIX,
    # other
    'TAR': 'Targeted Sequencing - REVOLVE Panel - cfDNA and Buffy Coat '+TAR_SUFFIX,
    'PWGS': 'Plasma Whole Genome Sequencing '+PWGS_SUFFIX
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
