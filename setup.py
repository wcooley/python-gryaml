#!/usr/bin/env python

"""Setuptools setup."""

from setuptools import setup, find_packages

import tomli


if __name__ == '__main__':
    # This is probably pretty fragile
    with open('pyproject.toml', 'rb') as inp:
        pyproject = tomli.load(inp)

    setup(
        name=pyproject['project']['name'],
        version='1.0.0',
        license=pyproject['project']['license'],
        description=pyproject['project']['description'],
        packages=find_packages(where='src/', include=['*']),
        package_dir={'': 'src'},
        py_modules=[
        ],
        install_requires=pyproject['project']['dependencies'],
        extras_require=pyproject['project']['optional-dependencies'],
        entry_points={
            'console_scripts': [
                'gryaml-load = gryaml.__main__:__main__',
            ],
        }
    )
