#! /usr/bin/env python3

"""
Setup script for Djerba
"""

from setuptools import setup, find_packages

package_version = '0.0.3'
package_root = 'src/lib'

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='djerba',
    version=package_version,
    scripts=[
        'src/bin/djerba.py',
        'src/bin/djerba_from_command.py',
        'src/bin/upload.py'
    ],
    packages=find_packages(where=package_root),
    package_dir={'' : package_root},
    package_data={
        'djerba': [
            'data/cancer_colours.csv',
            'data/input_schema.json',
            'data/upload_config.json'
        ]
    },
    install_requires=['couchdb2', 'jsonschema', 'numpy', 'pandas', 'scipy', 'statsmodels', 'PyYAML'],
    python_requires='>=3.7',
    author="Iain Bancarz",
    author_email="ibancarz@oicr.on.ca",
    description="Create reports from metadata and workflow output",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oicr-gsi/djerba",
    keywords=['cancer', 'bioinformatics', 'cBioPortal'],
    license='GPL 3.0',
)
