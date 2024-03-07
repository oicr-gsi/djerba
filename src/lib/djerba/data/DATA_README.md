# Updating Djerba reference files

## Introduction

The Djerba repository contains reference files which describe cancer gene terminology and known oncogenic variants.

It is recommended to check Djerba against the reference sources, and update if necessary, approximately every six months. This time period may be reviewed if the frequency of reference updates increases.

## Update procedure

1. Create a JIRA ticket and associated `git` branch for the update.
2. For each reference file:
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

### oncoKBcancerGeneList.tsv

`curl -X GET "https://www.oncokb.org/api/v1/utils/cancerGeneList.txt" -H  "accept: text/plain" > oncoKBcancerGeneList.tsv`

### Centromeres

- the hg38 centromeres `hg38_centromeres.txt` can be downloaded manually from [USCS](http://genome.ucsc.edu/cgi-bin/hgTables?hgsid=1334321853_hiXsRQvWI9Djbr8IrSABHWafymIR&clade=mammal&org=Human&db=hg38&hgta_group=map&hgta_track=centromeres&hgta_table=0&hgta_regionType=genome&position=chrX%3A15%2C560%2C138-15%2C602%2C945&hgta_outputType=primaryTable&hgta_outFileName=
)

### fonts: 

1. download fonts somewhere you have sudo with `apt install ttf-mscorefonts-installer`
2. cp -r `msfonts/` ~/.local/share/fonts/