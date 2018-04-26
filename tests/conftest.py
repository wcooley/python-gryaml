#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shared fixtures for :mod:`pytest`."""

from __future__ import print_function, absolute_import

import os

import pytest  # noqa

import gryaml
import py2neo
import yaml

from py2neo_compat import py2neo_ver


def pytest_report_header(config, startdir):
    """Add versions & config info to test output on terminal."""
    lines = []

    if 'NEO4J_URI' in os.environ:
        lines.append('Neo4J URI: %s' % os.environ['NEO4J_URI'])

    lines.append('py2neo: {0.__version__}'
                 ' pyyaml: {1.__version__}'
                 ' libyaml: {1.__with_libyaml__}'.format(py2neo, yaml))
    lines.append('forked: %s' % config.getvalue('forked'))

    return lines


@pytest.fixture
def graphdb():
    """Fixture connecting to graphdb."""
    if 'NEO4J_URI' not in os.environ:
        pytest.skip('Need NEO4J_URI environment variable set')
    graphdb = gryaml.connect(uri=os.environ['NEO4J_URI'])
    graphdb.delete_all()
    return graphdb


@pytest.fixture
def graphdb_offline():
    """Ensure the database is not connected."""
    if py2neo_ver < 2:
        pytest.skip('Offline not supported in py2neo < 2')
    neo4j_uri_env = os.environ.get('NEO4J_URI', None)
    if neo4j_uri_env:
        del os.environ['NEO4J_URI']
    old_graphdb = gryaml._py2neo.graphdb
    gryaml._py2neo.graphdb = None
    yield
    gryaml._py2neo.graphdb = old_graphdb
    if neo4j_uri_env:
        os.environ['NEO4J_URI'] = neo4j_uri_env
