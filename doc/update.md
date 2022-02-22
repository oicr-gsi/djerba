# Updating Djerba reference files

## WARNING

The file downloads described below are in a different format from those in legacy CGI-Tools, with different column headings and column order. Although the number of entries is the same, the content of some entries has changed. Updating the reference files is out of scope for the first production release of Djerba.

In a subsequent release of Djerba, HTML generation by legacy Rmarkdown will be replaced by JSON input to a template. As part of this process, Djerba should be updated to use the new reference file contents, including appropriate testing and validation.

## Introduction

The Djerba repository contains reference files in `src/lib/djerba/data/reference`, which describe cancer gene terminology and known oncogenic variants.

It is recommended to check Djerba against the reference sources, and update if necessary, approximately every six months. This time period may be reviewed if the frequency of reference updates increases.

The files are:
- OncoTree.txt, from [OncoTree](http://oncotree.mskcc.org/#/home)
- allCuratedGenes.tsv, from [OncoKB](https://www.oncokb.org/)
- oncoKBcancerGeneList.tsv, from [OncoKB](https://www.oncokb.org/)

## Update procedure

1. Create a JIRA ticket and associated `git` branch for the update.
2. For each of the 3 reference files:
   a. Download the latest version
   b. Compare with the version in Djerba
   c. If any differences are found, commit the updated file to the working branch; otherwise move on to the next file
3. If any files have been changed:
   a. Run Djerba unit and validation tests
   b. Resolve any failures; test and validate any required code changes
   c. Note the updated files in the changelog
   d. Merge the working branch; tag and release a new version of Djerba
4. Close the ticket, with a comment noting if files were changed

Updating the reference files is not expected to change the behaviour of Djerba tests; variants may be added, but modifying the existing variants in the tests is less likely. If any failures do occur, they must be corrected, with appropriate validation of any code changes.

## Download commands

### OncoTree.txt

`curl -X GET --header 'Accept: text/plain' 'http://oncotree.mskcc.org/api/tumor_types.txt' > OncoTree.txt`

### allCuratedGenes.tsv

`curl -X GET "https://www.oncokb.org/api/v1/utils/allCuratedGenes.txt?includeEvidence=true" -H  "accept: text/plain" > allCuratedGenes.tsv`

### oncoKBcancerGeneList.tsv

`curl -X GET "https://www.oncokb.org/api/v1/utils/cancerGeneList.txt" -H  "accept: text/plain" > oncoKBcancerGeneList.tsv`
