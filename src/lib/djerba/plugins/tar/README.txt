TAR PLUGIN

The TAR plugin is sub-divided into three plugins:

1. Sample (tar.sample)
- Generates the sample information 
- Uses 3 files as input: ichorCNA metrics, consensusCruncher normal metrics, consensusCruncher tumour metrics

2. Shallow Whole Genome Sequencing (tar.swgs)
- Generates the CNV section with amplifications only
- Uses 1 file as input: an ichorCNA .seg.txt file 

3. Snvs and Indels (tar.snv_indel)
- Generates the snvs and indels variants section 
- Uses 2 files as input: consensusCruncher normal maf, consensusCruncher tumour maf


Recommended render order (i.e. output in the report):
1. tar.sample
2. tar.snv_indel
3. tar.swgs

Tools shared between all three plugins:
- provenance_tools.py: this is used to search for the most recent files within FPR
- render.py: this is used to render from JSON to HTML

Plugin specific tools:

1. tar.sample
- plugin.py: the tar.sample plugin
- contants.py: constants for the tar.sample plugin
- sample_template.html: the HTML template
- test: a directory that contains:
	- plugin_test.py: plugin test
	- tar.sample.ini: config file for the plugin test 

2. tar.snv_indel
- plugin.py: the tar.snv_indel plugin
- constants.py: contains for filter_maf_for_tar function in tar.snv_indel plugin.py
- snv_indel_tools: a directory that contains:
	- constants.py: constants for all snv indel tools
	- preprocess.py: preprocesses the maf files
	- extract.py: functions to help create the JSON for the plugin
	- Rscripts: a directory that contains:
		- process_data.r: contains functions for eventually creating data_mutations_extended_oncogenic.txt
		- supporting_functions.r: functions used by process_data.r
- test: a directory that contains:
	- plugin_test.py: plugin test
	- data: a directory that contains tar.snv_indel.ini
- data: a directory that contains TGL.frequency.20210609.annot.txt for filtering of the maf file in plugin.py
- html: a directory that contains snv_indel_template.html, the HTML template

3. tar.swgs
- plugin.py: the tar.swgs plugin
- constants.py: constants for the tar.swgs plugin
- preprocess.py: functions to help preprocess and annotate the .seg.txt file
- extract.py: functions to help create the JSON for the plugin
- html: a directory that contains swgs_template.html, the HTML template
- Rscripts: a directory that contains:
	 - process_data.r: contains functions for eventually creating data_CNA.txt and others
         - supporting_functions.r: functions used by process_data.r
- test: a directory that contains:
        - plugin_test.py: plugin test
        - data: a directory that contains tar.swgs.ini
