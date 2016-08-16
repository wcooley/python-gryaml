#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shared fixtures for :mod:`pytest`."""

from __future__ import print_function, absolute_import

import os

import pytest  # noqa

import gryaml
from gryaml.py2neo_compat import _cypher_execute, py2neo_ver


@pytest.fixture
def graphdb():
    """Fixture connecting to graphdb."""
    if 'NEO4J_URI' not in os.environ:
        pytest.skip('Need NEO4J_URI environment variable set')
    graphdb = gryaml.connect(uri=os.environ['NEO4J_URI'])
    _cypher_execute(graphdb, 'MATCH (n) DETACH DELETE n')
    return graphdb

@pytest.yield_fixture
def graphdb_offline():
    """Ensure the database is not connected."""
    neo4j_uri_env = os.environ.get('NEO4J_URI', None)
    if neo4j_uri_env:
        del os.environ['NEO4J_URI']
    old_graphdb = gryaml.py2neo_compat.graphdb
    gryaml.py2neo_compat.graphdb == None
    yield
    gryaml.py2neo_compat.graphdb = old_graphdb
    if neo4j_uri_env:
        os.environ['NEO4J_URI'] = neo4j_uri_env

