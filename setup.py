#! /usr/bin/env python3

"""
Setup script for Djerba
"""

from setuptools import setup, find_packages

package_version = '0.2.0c'
package_root = 'src/lib'

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='djerba',
    version=package_version,
    scripts=[
        'src/bin/djerba.py',
        'src/bin/html2pdf.py',
        'src/bin/qc_report.sh',
        'src/bin/sequenza_explorer.py',
        'src/bin/run_mavis.py',
        'src/bin/wait_for_mavis.py'
    ],
    packages=find_packages(where=package_root),
    package_dir={'' : package_root},
    package_data={
        'djerba': [
            'data/20200818-oncoKBcancerGeneList.tsv',
            'data/20201126-allCuratedGenes.tsv',
            'data/20201201-OncoTree.txt',
            'data/civic/01-Jun-2020-GeneSummaries.tsv',
            'data/civic/01-Jun-2020-VariantGroupSummaries.tsv',
            'data/civic/01-Jun-2020-VariantSummaries.tsv',
            'data/config_template.ini',
            'data/cromwell_options.json',
            'data/cytoBand.txt',
            'data/defaults.ini',
            'data/ensemble_conversion_hg38.txt',
            'data/ensemble_conversion.txt',
            'data/entrez_conversion.txt',
            'data/filter_flags.exclude',
            'data/gencode_v33_hg38_genes.bed',
            'data/genomic_summary.txt',
            'data/mavis_config_template.json',
            'data/mavis_legacy_config_template.json',
            'data/mavis_settings.ini',
            'data/mutation_types.exonic',
            'data/mutation_types.nonsynonymous',
            'data/targeted_genelist.txt',
            'data/tmbcomp-externaldata.txt',
            'data/tmbcomp-tcga.txt',
	    'R_markdown/assay_description_wgs_only.html',
	    'R_markdown/assay_description_wgts.html',
	    'R_markdown/coverage-40x.txt',
	    'R_markdown/coverage-80x.txt',
	    'R_markdown/footer_template.html',
            'R_markdown/header.html',
            'R_markdown/html_report_default.Rmd',
            'R_markdown/html_report_failed.Rmd',
            'R_markdown/html_report_wgs_only.Rmd',
            'R_markdown/OICR_Logo_RGB_ENGLISH.png',
            'R_stats/calc_mut_sigs.r',
            'R_stats/convert_mavis_to_filtered_fusions.r',
            'R_stats/convert_rsem_results_zscore.r',
            'R_stats/convert_seg_to_gene_singlesample.r',
            'R_stats/convert_vep92_to_filtered_cbio.r',
            'R_stats/singleSample.r'
        ]
    },
    install_requires=[
        'configparse',
        'numpy',
        'pandas',
        'pdfkit',
        'scipy',
    ],
    python_requires='>=3.9',
    author="Iain Bancarz",
    author_email="ibancarz [at] oicr [dot] on [dot] ca",
    description="Create reports from metadata and workflow output",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oicr-gsi/djerba",
    keywords=['cancer', 'bioinformatics'],
    license='GPL 3.0',
)
