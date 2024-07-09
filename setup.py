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
    'r/*',
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
        'src/bin/mini_djerba.py',
        'src/bin/update_oncokb_cache.py',
        'src/bin/validate_plugin_json.py'
    ],
    packages=find_packages(where=package_root),
    package_dir={'' : package_root},
    package_data={
        'djerba': [
            'data/20200818-oncoKBcancerGeneList.tsv',
            'data/20240315-allCuratedGenes.tsv',
            'data/OncoTree.json',
            'data/NCCN_annotations.txt',
            'data/benchmark_config.ini',
            'data/benchmark_params.json',
            'data/cytoBand.txt',
            'data/ensemble_conversion_hg38.txt',
            'data/entrez_conversion.txt',
            'data/gencode_v33_hg38_genes.bed',
            'data/gencode.v31.ensg_annotation_w_entrez.bed',
            'data/hg38_centromeres.txt',
            'data/tcga_code_key.txt',
            'data/tmbcomp-externaldata.txt',
            'data/tmbcomp-tcga.txt',
        ],
        'djerba.core': install_wildcards,
        'djerba.helpers.provenance_helper': install_wildcards,
        'djerba.mergers.gene_information_merger': install_wildcards,
        'djerba.mergers.treatment_options_merger': install_wildcards,
        'djerba.plugins.demo1': install_wildcards,
        'djerba.plugins.demo2': install_wildcards,
        'djerba.plugins.demo3': install_wildcards,
        'djerba.plugins.patient_info': install_wildcards,
        'djerba.plugins.summary': install_wildcards,
        'alternate_djerba.plugins.demo4': install_wildcards,
    },
    install_requires=[
        'configparse',
        'email_validator',
        'jsonschema',
        'mako',
        'markdown',
        'numpy==1.23.1', # set exact version to avoid build conflict with gsi-qc-etl
        'pandas',
        'pdfkit',
        'pyinstaller',
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
