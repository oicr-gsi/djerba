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
    '*.bed',
    '*.ini',
    '*.json',
    '*.html',
    '*.txt',
    '*.r',
    '*.R',
    'data/*',
    'html/*',
    'resources/*',
    'R/*',
    'r/*',
    'Rscripts/*',
    'templates/*'
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='djerba',
    version=__version__,
    scripts=[
        'src/bin/benchmark.py',
        'src/bin/diff_reports.py',
        'src/bin/djerba.py',
        'src/bin/generate_ini.py',
        'src/bin/mini_djerba.py',
        'src/bin/update_oncokb_cache.py',
        'src/bin/validate_plugin_json.py'
    ],
    packages=find_packages(where=package_root),
    package_dir={'' : package_root},
    package_data={
        'djerba': [
            'util/benchmark/benchmark_pwgs.ini',
            'util/benchmark/benchmark_tar.ini',
            'util/benchmark/benchmark_wgs.ini',
            'util/benchmark/benchmark_wgts.ini',
            'util/data/20200818-oncoKBcancerGeneList.tsv',
            'util/data/NCCN_annotations.txt',
            'util/data/cytoBand.txt',
            'util/data/entrez_conversion.txt',
            'util/data/gencode_v33_hg38_genes.bed',
            'util/oncokb/20240315-allCuratedGenes.tsv'
        ],
        'djerba.core': install_wildcards,
        'djerba.helpers.expression_helper': install_wildcards,
        'djerba.helpers.input_params_helper': install_wildcards,
        'djerba.helpers.provenance_helper': install_wildcards,
        'djerba.helpers.pwgs_cardea_helper': install_wildcards,
        'djerba.helpers.tar_input_params_helper': install_wildcards,
        'djerba.mergers.gene_information_merger': install_wildcards,
        'djerba.mergers.treatment_options_merger': install_wildcards,
        'djerba.plugins.benchmark': install_wildcards,
        'djerba.plugins.captiv8': install_wildcards,
        'djerba.plugins.case_overview': install_wildcards,
        'djerba.plugins.cnv': install_wildcards,
        'djerba.plugins.demo1': install_wildcards,
        'djerba.plugins.demo2': install_wildcards,
        'djerba.plugins.demo3': install_wildcards,
        'djerba.plugins.failed_report': install_wildcards,
        'djerba.plugins.fusion': install_wildcards,
        'djerba.plugins.genomic_landscape': install_wildcards,
        'djerba.plugins.hla': install_wildcards,
        'djerba.plugins.patient_info': install_wildcards,
        'djerba.plugins.pwgs.analysis': install_wildcards,
        'djerba.plugins.pwgs.case_overview': install_wildcards,
        'djerba.plugins.pwgs.sample': install_wildcards,
        'djerba.plugins.pwgs.summary': install_wildcards,
        'djerba.plugins.report_title': install_wildcards,
        'djerba.plugins.sample': install_wildcards,
        'djerba.plugins.summary': install_wildcards,
        'djerba.plugins.supplement.body': install_wildcards,
        'djerba.plugins.tar.sample': install_wildcards,
        'djerba.plugins.tar.snv_indel': install_wildcards,
        'djerba.plugins.tar.snv_indel.snv_indel_tools': install_wildcards,
        'djerba.plugins.tar.swgs': install_wildcards,
        'djerba.plugins.tar.status': install_wildcards,
        'djerba.plugins.wgts.cnv_purple': install_wildcards,
        'djerba.plugins.wgts.common.cnv': install_wildcards,
        'djerba.plugins.wgts.snv_indel': install_wildcards,
        'alternate_djerba.plugins.demo4': install_wildcards,
    },
    install_requires=[
        'configparse',
        'email_validator',
        'jsonschema',
        'lets-plot',
        'mako',
        'markdown',
        'matplotlib',
        'numpy>2',
        'pandas',
        'pdfkit',
        'plotnine',
        'pycairo',
        'pyinstaller',
        'PyPDF2',
        'requests',
        'seaborn',
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
