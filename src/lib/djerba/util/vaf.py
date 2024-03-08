"""
Extremely simple function used to parse VAF from a MAF file row in eg. csv.DictReader
Used in VAF helper and snv/indel plugin, placed here to ensure consistency
"""

def get_tumour_vaf(row):
    vaf = row['tumour_vaf']
    vaf = int(round(float(vaf), 2)*100)
    return vaf
