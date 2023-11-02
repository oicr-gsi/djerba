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


## Other data files

- the hg38 centromeres `hg38_centromeres.txt` can be downloaded manually from [USCS](http://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1334321853_hiXsRQvWI9Djbr8IrSABHWafymIR&clade=mammal&org=Human&db=hg38&hgta_group=map&hgta_track=centromeres&hgta_table=0&hgta_regionType=genome&position=chrX%3A15%2C560%2C138-15%2C602%2C945&hgta_outputType=primaryTable&hgta_outFileName=
)
- the distribution of Percent Genome Altered (PGA) has two processing steps
  1. Go to [GDC Data portal File Repository](https://portal.gdc.cancer.gov/repository) and filter for Data Category = "copy number variation" and Data Format = "txt", as done [here](https://portal.gdc.cancer.gov/repository?filters=%7B%22op%22%3A%22and%22%2C%22content%22%3A%5B%7B%22op%22%3A%22in%22%2C%22content%22%3A%7B%22field%22%3A%22files.data_category%22%2C%22value%22%3A%5B%22copy%20number%20variation%22%5D%7D%7D%2C%7B%22op%22%3A%22in%22%2C%22content%22%3A%7B%22field%22%3A%22files.data_format%22%2C%22value%22%3A%5B%22txt%22%5D%7D%7D%5D%7D). Download the CNV data as well as the metadata and the clinical data.
  2. loop the `prototypes/PGA_TCGA/CNV_summary.R` script across all files, then summarize using `prototypes/PGA_TCGA/CNV_all.R`. An example of this can be found in `prototypes/PGA_TCGA/directory_loop.sh`.
- fonts: 
  1. download fonts somewhere you have sudo with `apt install ttf-mscorefonts-installer`
  2. cp -r `msfonts/` ~/.local/share/fonts/