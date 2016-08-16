#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for :mod:`gryaml.py2neo_compat`."""

from __future__ import print_function, absolute_import

import pytest  # noqa

from gryaml.py2neo_compat import compat_node, _create, py2neo_node

def test_connect(graphdb):
    """Test :func:`~py2neo_compat.connect`."""
    assert graphdb.neo4j_version


@pytest.mark.integration
@pytest.mark.usefixtures('graphdb')
def test__create():
    """Test :func:`~py2neo_compat._create`."""
    # Native _create_ can create multiple entities but this cannot
    alice = _create({'name': 'Alice'})
    bob = _create({'name': 'Bob'})
    knows = _create((alice, 'KNOWS', bob, {'since': '2006'}))

    assert alice['name'] == 'Alice'  # Remember Alice? This song's about Alice.
    assert bob['name'] == 'Bob'
    assert knows.start_node == alice
    assert knows.end_node == bob
    assert knows['since'] == '2006'


@pytest.mark.integration
@pytest.mark.usefixtures('graphdb')
def test__create_empty():
    """Test :func:`~py2neo_compat._create` with an empty node."""
    empty = _create(py2neo_node())
    assert empty is not None
    assert empty.get_labels() == set()
    assert empty.get_properties() == {}


@pytest.mark.integration
@pytest.mark.usefixtures('graphdb')
@pytest.mark.parametrize(('labels', 'properties'), [
    (('restauranteur',), {'name': 'Alice'}),        # Label, property
    ((), {}),                                       # Empty iterable, empty map
    (None, None),                                   # Nada, Nada
    ({'person'}, {}),                               # Label, empty map
    ([], {'name': 'Alice'}),                        # Empty iterable, property
])
def test_compat_node(labels, properties):
    """Test :func:`~py2neo_compat.compat_node`."""

    node = compat_node(labels=labels, properties=properties)
    assert node is not None
    assert node.get_labels() == (set(labels) if labels else set())
    assert node.get_properties() == (dict(properties) if properties else {})
