#!/usr/bin/env python
"""Setuptools setup."""

from setuptools import setup, find_packages

with open('README.rst') as fp:
    readme = fp.read()

with open('HISTORY.rst') as fp:
    history = fp.read().replace('.. :changelog:', '')

install_requires = [
    'boltons',
    'py2neo<3',
    'py2neo_compat~=1.0.0pre0',
    'pyyaml',
]

tests_require = [
    'pytest',
    'pytest-cov',
    'pytest-forked',
    'pathlib2; python_version<"3"',
]

setup(
    name='gryaml',
    use_scm_version=True,
    description='Represent Neo4j graph data as YAML.',
    long_description=readme + '\n\n' + history,
    author='Wil Cooley',
    author_email='wcooley@nakedape.cc',
    url='https://github.com/wcooley/python-gryaml',
    packages=find_packages(where='src', include=['gryaml']),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=install_requires,
    setup_requires=['setuptools_scm'],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
    },
    license='MIT',
    zip_safe=False,
    keywords='yaml py2neo neo4j gryaml',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    entry_points={
        'console_scripts': [
            'gryaml-load = gryaml.__main__:__main__',
        ],
    },
)
