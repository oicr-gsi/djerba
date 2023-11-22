#! /usr/bin/env python3

"""
Setup script for Djerba
"""

from setuptools import setup, find_packages

with open('src/lib/djerba/version.py') as version_file:
    exec(version_file.read()) # sets __version__
package_root = 'src/lib'

# list of wildcards, intended to capture ancillary files for plugins/helpers/mergers
# TODO make this neater and/or introduce stronger naming conventions
install_wildcards = [
    '*.json',
    '*.html',
    '*.txt',
    '*.r',
    '*.R',
    'data/*',
    'html/*',
    'resources/*',
    'R/*',
    'Rscripts/*'
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='djerba',
    version=__version__,
    scripts=[
        'src/bin/benchmark.py',
        'src/bin/djerba.py',
        'src/bin/generate_ini.py',
        'src/bin/sequenza_explorer.py',
        'src/bin/update_oncokb_cache.py',
        'src/lib/djerba/plugins/summary/update_summary.py'
    ],
    packages=find_packages(where=package_root),
    package_dir={'' : package_root},
    package_data={
        'djerba': [
            'data/20200818-oncoKBcancerGeneList.tsv',
            'data/20231116-allCuratedGenes.tsv',
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
            'data/mavis_config_template.json',
            'data/mavis_legacy_config_template.json',
            'data/mavis_settings.ini',
            'data/mutation_types.exonic',
            'data/mutation_types.nonsynonymous',
            'data/targeted_genelist.txt',
            'data/tmbcomp-externaldata.txt',
            'data/tmbcomp-tcga.txt',
        ],
        'djerba.core': install_wildcards,
        'djerba.helpers.expression_helper': install_wildcards,
        'djerba.helpers.input_params_helper': install_wildcards,
        'djerba.helpers.provenance_helper': install_wildcards,
        'djerba.helpers.tar_input_params_helper': install_wildcards,
        'djerba.mergers.gene_information_merger': install_wildcards,
        'djerba.mergers.treatment_options_merger': install_wildcards,
        'djerba.plugins.case_overview': install_wildcards,
        'djerba.plugins.cnv': install_wildcards,
        'djerba.plugins.demo1': install_wildcards,
        'djerba.plugins.demo2': install_wildcards,
        'djerba.plugins.demo3': install_wildcards,
        'djerba.plugins.failed_report': install_wildcards,
        'djerba.plugins.fusion': install_wildcards,
        'djerba.plugins.genomic_landscape': install_wildcards,
        'djerba.plugins.pwgs.analysis': install_wildcards,
        'djerba.plugins.pwgs.sample': install_wildcards,
        'djerba.plugins.sample': install_wildcards,
        'djerba.plugins.summary': install_wildcards,
        'djerba.plugins.supplement': install_wildcards,
        'djerba.plugins.supplement.body': install_wildcards,
        'djerba.plugins.supplement.header': install_wildcards,
        'djerba.plugins.tar.sample': install_wildcards,
        'djerba.plugins.tar.snv_indel': install_wildcards,
        'djerba.plugins.tar.snv_indel.snv_indel_tools': install_wildcards,
        'djerba.plugins.tar.swgs': install_wildcards,
        'djerba.plugins.wgts.snv_indel': install_wildcards,
    },
    install_requires=[
        'configparse',
        'jsonschema',
        'mako',
        'markdown',
        'pandas',
        'pdfkit',
        'PyPDF2',
        'requests',
        'statsmodels',
    ],
    python_requires='>=3.10.6',
    author="Iain Bancarz",
    author_email="ibancarz [at] oicr [dot] on [dot] ca",
    description="Create reports from metadata and workflow output",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oicr-gsi/djerba",
    keywords=['cancer', 'bioinformatics'],
    license='GPL 3.0',
)
