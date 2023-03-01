#! /usr/bin/env python3

"""
Setup script for Djerba
"""

from setuptools import setup, find_packages

with open('src/lib/djerba/version.py') as version_file:
    exec(version_file.read()) # sets __version__
package_root = 'src/lib'

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='djerba',
    version=__version__,
    scripts=[
        'src/bin/benchmark.py',
        'src/bin/djerba.py',
        'src/bin/html2pdf.py',
        'src/bin/list_inputs.py',
        'src_bin/pdf_merger.py',
        'src/bin/qc_report.sh',
        'src/bin/run_mavis.py',
        'src/bin/sequenza_explorer.py',
        'src/bin/update_genomic_summary.py',
        'src/bin/update_oncokb_cache.py',
        'src/bin/update_technical_notes.py',
        'src/bin/view_json.py'
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
            'data/technical_notes.txt',
            'data/hg38_centromeres.txt',
            'data/pgacomp-tcga.txt',
            'html/clinical_report_template.html',
            'html/genomic_details_template.html',
            'html/header.html',
            'html/OICR_Logo_RGB_ENGLISH.png',
            'html/style.css',
            'html/supplementary_materials_template.html',
            'html/templates_for_supp/definitions_metrics.html',
            'html/templates_for_supp/definitions_oncokb.html',
            'html/templates_for_supp/definitions_tests.html',
            'html/templates_for_supp/description_wgs.html',
            'html/templates_for_supp/description_wts.html',
            'html/templates_for_supp/disclaimer.html',
            'html/therapies_template.html',
            'data/mavis_config_template.json',
            'data/mavis_legacy_config_template.json',
            'data/mavis_settings.ini',
            'data/mutation_types.exonic',
            'data/mutation_types.nonsynonymous',
            'data/targeted_genelist.txt',
            'data/tmbcomp-externaldata.txt',
            'data/tmbcomp-tcga.txt',
            'R_plots/biomarkers_plot.R',
            'R_plots/cnv_plot.R',
            'R_plots/pga_plot.R',
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
        'PyPDF2',
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
