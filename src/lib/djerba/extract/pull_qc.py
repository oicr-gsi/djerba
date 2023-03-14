#!/usr/bin/env python3

import argparse
import json
import urllib.request as request
import gsiqcetl.column
from gsiqcetl import QCETLCache

class Requisition():
    
    def __init__(self, pinery_requisition, pinery_assay):
        self.id: int = pinery_requisition['id']
        self.name: str = pinery_requisition['name']
        self.assay: str = pinery_assay['name']
        self.assay_id: int = pinery_assay['id']
        self.assay_description: str = pinery_assay['description']
        self.assay_version: str = pinery_assay['version']

class ReportData:
    def __init__(self, requisition: Requisition):
        self.requisition: Requisition = requisition

etl_cache: str = None
QCETL_CACHE="/scratch2/groups/gsi/production/qcetl_v1"

def main():
    global pinery_url
    global etl_cache

    parser = argparse.ArgumentParser(
        description='')
    parser.add_argument('-r',
                        '--requisition',
                        help='specify requisition to report on',
                        required=True)
    parser.add_argument('-d',
                        '--donor',
                        help='specify requisition to report on',
                        required=True)

    args = parser.parse_args()

    pinery_url = "http://pinery.gsi.oicr.on.ca"
    etl_cache = QCETLCache(QCETL_CACHE)
    
    report_data = collect_data(args.requisition, args.donor)

def collect_data(requisition_name: str, donor_name: str) -> ReportData:
    pinery_requisition = pinery_get(f'/requisition?name={requisition_name}')
    pinery_assay = pinery_get(f'/assay/{pinery_requisition["assay_id"]}')
    requisition = Requisition(pinery_requisition, pinery_assay)
    
    print(requisition.assay)
    fetch_informatics_etl_data(donor_name)
    return(requisition)

def fetch_informatics_etl_data(donor):
    callability = etl_cache.mutectcallability.mutectcallability
    columns = gsiqcetl.column.MutetctCallabilityColumn
    
    callability_select = [
        columns.Donor, columns.TissueOrigin,
        columns.TissueType, columns.GroupID,
        columns.LibraryDesign, columns.Callability
    ]
    data = callability.loc[
        (callability[columns.Donor] == donor),
        callability_select]
    callability_val = round(data.iloc[0][columns.Callability].item() * 100,1)
    print(callability_val)

    coverage = etl_cache.bamqc4merged.bamqc4merged
    cov_columns = gsiqcetl.column.BamQc4MergedColumn
    
    cov_select = [
        cov_columns.Donor, cov_columns.TissueOrigin,
        cov_columns.TissueType, cov_columns.GroupID,
        cov_columns.LibraryDesign, cov_columns.CoverageDeduplicated
    ]
    data = coverage.loc[
        (coverage[columns.Donor] == donor) &
        (coverage[columns.TissueType] != "R"),
        cov_select]
    cov_val = round(data.iloc[0][cov_columns.CoverageDeduplicated].item(),1)
    print(cov_val)

def pinery_get(relative_url: str) -> dict:
    if not relative_url.startswith('/'):
        raise RuntimeError('Invalid relative url')
    return json.load(request.urlopen(f'{pinery_url}{relative_url}'))

if __name__ == '__main__':
    main()
