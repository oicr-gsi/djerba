# Data Readme

## NCCN Annotations
- Latest Date: Feb 6, 2024
- By Felix Beaudry
- From [NCCN Evidence Blocks](https://www.nccn.org/guidelines/guidelines-with-evidence-blocks)
- Manually copied, also at https://www.nccn.org/webservices/Products/Api/Biomarker/GetBiomarkersByGuidelineName/ but requires access



## OncoTree
- Latest Date: Dec 14, 2023
- By Felix Beaudry
- From [Oncotree Api](https://oncotree.mskcc.org/#/home?tab=api)
- Download as `curl -X GET --header 'Accept: application/json' 'https://oncotree.mskcc.org:443/api/tumorTypes/tree' >OncoTree.json`

## All Curated Genes
- Latest Date: Nov. 16, 2023
- By Alex Fortuna
- `curl -X GET "https://www.oncokb.org/api/v1/utils/allCuratedGenes.txt?includeEvidence=true" -H  "accept: text/plain" > allCuratedGenes.tsv`
