## CouchDB Database 
#### Lauren Toy | Fall 2022 Co-op  
##### https://github.com/oicr-gsi/djerba/tree/master/prototypes/db *TO DO check link after pushed*
##### Additional documentation and examples : https://wiki.oicr.on.ca/display/GSI/Database+Extraction 
***

### Table of Contents
* addfolder.py
* design.py & pull.py
* process.py
* extract_plots.R
* extract_onco.R

***
## addfolder.py
Searches for and upload djerba_report JSON's to CouchDB. Apply to folder on cluster for archiving old reports.

##### `python3 addfolder.py --help`
Argument | Required | Description
---     | ---   | ---
folder  | yes   | path of directory to search
name    | no    | name of database (currently defaults to "djerba_test"), in future could choose to change this hard-coded default location
url     | no    | base url of database (currently defaults to http://admin:djerba123@10.30.133.78:5984/)
print   | no    | optional expanded terminal feedback for debugging, any logger warnings/errors and basic feedback will still show when not specified

##### Example where upload is to actual djerba database specified by -n flag
##### `python3 addfolder.py /.mounts/labs/CGI/cap/cap-archive -n djerba` 

***
## design.py & pull.py
These work together to extract data from CouchDB. Main script called is design.py which internally calls pull.py.

Overview
* 2 step command line user input (1) choosing mode and other settings (2) query input if filter mode is chosen
* 3 modes (filter, status, delete)
* 4 filters (multi, equal, less, great)
* output (terminal print, save as JSON and/or CSV)
* Note: database location (db name and url) is currently hard-coded within `design.py Design() __init__` method, from cmd line can check which database it is set to by `python3 design.py stat`

### STEP 1: USER INPUT (mode and settings)

##### `python3 design.py --help`
Argument | Required | Description
---     | ---   | ---
mode    | yes   | word or letter accepted for filter, status, or delete *(see next table)* 
name    | yes   | name of design document **
print   | no    | print table style format of query results to terminal
csv     | no    | save query results as CSV 
json    | no    | save query results as JSON
all     | no    | show all files (true and false) for  filters (equal, less, great) not just those that match operand which is the default (true only)
##### **can query/pull data from an already created/existing design document in database if filter type/name and query is the same (in this case the logging warning of `<Response [409]> Design Document Update Conflict.` is expected.

Mode  | Word | Letter | Description
---   | ---  | ---  | ---
filter| multi| m    | Specify fields (keys in JSON) to see values
filter| equal| e    | Specify key and value (string, bool, or number)
filter| less | l    | Specify key and value (< number)
filter| great| g    | Specify key and value (> number)
status| stat | s    | Show database status, name/url and number of documents. Note: that the total includes any design documents etc. `python3 design.py stat`
delete| del  | d    | Deletes a design document from database `python3 design.py del -n <doc2delete>`

##### Example of multi filter with document named "test_multi" and terminal print
##### `python3 design.py multi -n test_multi -p`
##### Additionally saving output to csv and json, no -d specified so defaults to an "extract" folder in the same location as `__main__` 
##### `python3 design.py m -n test_multi -p -c -j`
##### Example of less operand filter that specifies output directory path for CSV file
##### `python3 design.py less -n test_less -c -d /path/to/output/directory`
##### Example of equal filter that displays all file results not just those that match operand and output are to the terminal and a JSON
##### `python3 design.py e -n test_equal -p -j -a`


### STEP 2: USER INPUT (filter query)
#### For all filters: **access nested keys with a forward slash `/`**
#### Example: `report/patient_info/Study`
Filter   | Format | Example | Description
---      | ---  | ---  | ---
multi (m)| seperate filters within same view with a comma and seperate different views with @     |  `report/failed, report/author @ report/assay_type, report/patient_info/Study, report/patient_info/Primary cancer, report/patient_info/Genetic Sex @ report/patient_info/Site of biopsy/surgery`   |  3 views. View 1: failed and author. View 2: assay_type, Study, Primary cancer, and Genetic Sex. View 3: Site of biopsy/surgery.
equal (e)| *note wrapping query in brackets like tuple will always work for single or multi view* | `report/failed, true`  OR  `(report/failed, true)` | **for one view.** *note format without surronding brackets only works for keys without special characters such as brackets in "Coverage (mean)" due to parsing.* View 1: failed=true.
equal (e)| enter filters like tuple within brackets, seperate key and value with comma inside brackets, seperate views with comma  | `(report/failed, true), (report/author, Felix Beaudry), (report/oncogenic_somatic_CNVs/Total variants, 35), (report/patient_info/Site of biopsy/surgery, Liver)` | **for multiple views.** View 1: failed=true. View 2: author=Felix Beaudry. View 3: Total variants=35. View 4: Site of biopsy/surger=Liver.
less (l) | *same as (e)* | `(report/oncogenic_somatic_CNVs/Total variants, 35)`  | View 1: Total variants<35 
great (g)| *same as (e)*  | `(report/oncogenic_somatic_CNVs/Total variants, 35) , (report/sample_info_and_quality/Estimated Ploidy, 3.5)` |  View 1: Total variants>35. View 2: Estimated ploidy>3.5

***
## process.py
Additional processing for some plots in below R scripts after multi filter query. End goal is information of Study, Gene, Mutation Type, and TMB for each sample.
1. design.py & pull.py 
    * Query on fields within djerba_report JSON (Study, Body, and TMB)
    * User Input 1: `python3 design.py multi -n small -j`
    * User Input 2: `report/patient_info/Study, report/small_mutations_and_indels/Body, report/genomic_landscape_info/Tumour Mutation Burden`
    * ***repeat twice for small_mutations_and_indels and oncogenic_somatic_CNVs*** 
    * User Input 1: `python3 design.py multi -n onco -j`
    * User Input 2: `report/patient_info/Study, report/oncogenic_somatic_CNVs/Body, report/genomic_landscape_info/Tumour Mutation Burden`
    * output: 2 JSON files 

2. process.py 
    * 4 command line arguments
    * see `python3 process.py --help`
        * PROCESS: mode options are "small" or "onco" to account for different key name for gene mutation within small_mutations_and_indels ("Type") vs oncogenic_somatic_CNVs ("Alteration")
        * JSON: (required) path to json, wrap in quotes
        * DIR:  (optional) output directory, default is within extract dir in same location as `__main__`
        * NAME: (optional) output name for csv file default is input/json/name_processed.csv
    * Example
        * `python3 process.py small -j "/path/to/json/wrapped/in/quotes"`
        * `python3 process.py onco -j "/path/to/json/wrapped/in/quotes" -n csv_file_name -d /dir/location/for/output/csv `

Input   | process.py | Output 
---     | ---        | ---  
json    | run for the 2 output JSONs from querying | csv 
Study, Body, TMB | extracts n number of gene and its mutation type from Body | Study, Gene, Mutation, TMB

***
## R Studio
View R markdown (`.rmd`) files for more info.

### extract_plots.R
* Scatter plot for Callability (%) and Coverage (mean)
* Bar graphs with facet grid options for gene/mutation frequency for small_mutations_and_indels and oncogenic_somatic_CNVs (input csv is output from process.py)

### extract_onco.R
* combination of three plots
* input csv is output from process.py
* main oncoplot using geom_rect where row = Gene and column = sample
* bar graph of gene mutation frequency, percent values for this is included in main oncoplat as a secondary y-axis 
* bar graph of TMB for each sample

***
### Dependencies
* design.py & pull.py

Package |Version |design.py |pull.py 
---           | ---    |--- | --- 
argparse      |        | Y  | N 
**requests*** | 2.22.0 | Y  | Y 
logging       |        | Y  | Y 
json          |        | Y  | Y 
os            |        | Y  | Y 
datetime      |        | Y  | Y 
posixpath     |        | Y  | Y 
csv           |        | N  | Y 
**pandas***   | 1.5.1  | N  | Y 
**tabulate*** | 0.9.0  | N  | Y 

*can install modules on cluster with `module load <package>` OR `module load <package/version>`  
##### `module load requests` OR  `module load requests/2.28.1`
##### `module load pandas` OR `module load pandas/1.4.2`
##### `module load tabulate` OR `module load tabulate/0.9.0`





