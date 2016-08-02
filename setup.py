#!/usr/bin/env python
"""Setuptools setup."""

from setuptools import setup

readme = open('README.rst').read()
doclink = """
Documentation
-------------

The full documentation is at http://gryaml.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='gryaml',
    use_scm_version=True,
    description='Represent Neo4j graph data as YAML.',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='Wil Cooley',
    author_email='wcooley@nakedape.cc',
    url='https://github.com/wcooley/python-gryaml',
    packages=[
        'gryaml',
    ],
    package_dir={'gryaml': 'gryaml'},
    include_package_data=True,
    install_requires=[
        'boltons',
        'py2neo<3',
        'pyyaml',
    ],
    setup_requires=['setuptools_scm'],
    license='MIT',
    zip_safe=False,
    keywords='gryaml',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
