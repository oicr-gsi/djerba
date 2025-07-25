"""Assay names/descriptions for use by multiple plugins"""

import djerba.util.constants as constants

# assay name constants, can be imported by plugins if needed
WGTS = 'WGTS'
WGS = 'WGS'
WGTS40X = 'WGTS40X'
WGS40X = 'WGS40X'
TAR = 'TAR'
PWGS = 'PWGS'

WGTS_SUFFIX = '(v{0})'.format(constants.WGTS_ASSAY_VERSION)
TAR_SUFFIX = '(v{0})'.format(constants.TAR_ASSAY_VERSION)
PWGS_SUFFIX = '(v{0})'.format(constants.PWGS_ASSAY_VERSION)

ASSAY_CASE_OVERVIEW = {
    # WGTS/WGS default to 80X
    WGTS: 'Whole genome and transcriptome sequencing (WGTS)'+\
    '-80X Tumour, 30X Normal '+WGTS_SUFFIX,
    WGS: 'Whole genome sequencing (WGS)-80X Tumour, 30X Normal '+WGTS_SUFFIX,
    # WGTS/WGS at 40X - seldom done now, but included for completeness
    WGTS40X: 'Whole genome and transcriptome sequencing (WGTS)'+\
    '-40X Tumour, 30X Normal '+WGTS_SUFFIX,
    WGS40X: 'Whole genome sequencing (WGS)-40X Tumour, 30X Normal '+WGTS_SUFFIX,
    # other
    TAR: 'Targeted Sequencing - REVOLVE Panel - cfDNA and Buffy Coat '+TAR_SUFFIX,
    PWGS: 'Plasma Whole Genome Sequencing '+PWGS_SUFFIX
}

ASSAY_SUPPLEMENTARY = {
    WGTS: 'WGTS pipeline '+constants.WGTS_ASSAY_VERSION,
    WGS: 'WGS pipeline '+constants.WGTS_ASSAY_VERSION,
    WGTS40X: 'WGTS pipeline '+constants.WGTS_ASSAY_VERSION,
    WGS40X: 'WGS pipeline '+constants.WGTS_ASSAY_VERSION,
    TAR: 'TAR pipeline '+constants.TAR_ASSAY_VERSION,
    PWGS: 'PWGS pipeline '+constants.PWGS_ASSAY_VERSION
}

def get_case_overview_description(name):
    return ASSAY_CASE_OVERVIEW.get(name)

def get_supplementary_description(name):
    return ASSAY_SUPPLEMENTARY.get(name)

def name_status(name):    
    """Convenience method to get name validity and error message (if any)"""
    if name in ASSAY_CASE_OVERVIEW:
        ok = True
        msg = None
    else:
        ok = False
        keys = sorted(list(ASSAY_CASE_OVERVIEW.keys()))
        msg = "Assay name {0} not in permitted lookup values {1}".format(name, keys)
    return [ok, msg]
