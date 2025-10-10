# Data Readme

## Djerba release v1.11.3
- oncoKBcancerGeneList.tsv file update
  - Latest date: Oct 08, 2025 
  - By Oumaima Hamza
  - From [OncoKB Cancer Gene List](https://www.oncokb.org/cancer-genes)
- allCuratedGenes.tsv file update
  - Latest date: Oct 08, 2025 
  - By Oumaima Hamza
  - `curl -H "Authorization: Bearer [your token]" https://www.oncokb.org/api/v1/utils/allCuratedGenes > allCuratedGenes.tsv` 
  - Run script in **djerba_prototypes** to load the JSON string from the .tsv file and align it with the previous TSV format
  
## Update: Djerba release v.1.8.2, March 2025

This document refers to files formerly in the `src/lib/djerba/data` directory, which have been relocated as follows:
- NCCN_annotations.txt: `src/lib/djerba/util/data`
- OncoTree.json: `genomic_landscape` plugin
- allCuratedGenes.tsv: `src/lib/djerba/util/oncokb`


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
