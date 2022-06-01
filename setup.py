#! /usr/bin/env python3

"""
Setup script for Djerba
"""

from setuptools import setup, find_packages

package_version = '0.2.9'
package_root = 'src/lib'

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='djerba',
    version=package_version,
    scripts=[
        'src/bin/djerba.py',
        'src/bin/html2pdf.py',
        'src/bin/list_inputs.py',
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
            'data/benchmark_config.ini',
            'data/benchmark_params.json',
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
            'html/body_style.html',
            'html/clinical_report_template.html',
            'html/definitions_1.html',
            'html/definitions_2.html',
            'html/description_wgs_only.html',
            'html/description_wgts.html',
            'html/genomic_details_template.html',
            'html/genomic_therapies_template.html',
            'html/header.html',
            'html/header_style.html',
            'html/OICR_Logo_RGB_ENGLISH.png',
            'html/variants_table_style.html',
            'data/mavis_config_template.json',
            'data/mavis_legacy_config_template.json',
            'data/mavis_settings.ini',
            'data/mutation_types.exonic',
            'data/mutation_types.nonsynonymous',
            'data/targeted_genelist.txt',
            'data/tmbcomp-externaldata.txt',
            'data/tmbcomp-tcga.txt',
            'R_plots/tmb_plot.R',
            'R_plots/vaf_plot.R',
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
        'mako',
        'markdown',
        'numpy',
        'pandas',
        'pdfkit',
        'scipy',
        'statsmodels'
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
