# Djerba tests

## Instructions

Instructions for configuring tests on the OICR cluster are on the [Djerba wiki page](https://wiki.oicr.on.ca/pages/viewpage.action?spaceKey=GSI&title=Djerba).

## Test data

Test data is located on the OICR internal filesystem. It has not been uploaded to Github for reasons of confidentiality.

### MAF data file

The MAF data file used in tests is `somatic01.maf.txt.gz`. It contains only 8 variants (10 lines total including headers), because the `maf2maf` tool is rather slow and we would like the tests to run quickly.

Current tests take about 5 seconds; expanding the MAF file to 25 lines takes 30 seconds, and to 184 lines takes 4 minutes.
