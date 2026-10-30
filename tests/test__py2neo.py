
"""Tests for :mod:`gryaml._py2neo`."""

import pytest


@pytest.mark.integration
def test_connect(graphdb):
    """Test :func:`~py2neo_compat.connect`."""
    assert graphdb.neo4j_version
