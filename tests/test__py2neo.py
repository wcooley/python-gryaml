#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for :mod:`gryaml._py2neo`."""

from __future__ import print_function, absolute_import

import pytest  # noqa

@pytest.mark.integration
def test_connect(graphdb):
    """Test :func:`~py2neo_compat.connect`."""
    assert graphdb.neo4j_version
