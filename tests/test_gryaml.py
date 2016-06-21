"""Tests for `gryaml` module."""

import os

import pytest
import yaml
from boltons.iterutils import first

import gryaml


@pytest.fixture
def graphdb():
    """Fixture connecting to graphdb."""
    if 'NEO4J_URI' not in os.environ:
        raise Exception('Need NEO4J_URI env var set')
    graphdb = gryaml.connect(uri=os.environ['NEO4J_URI'])
    graphdb.cypher.execute('MATCH (n) DETACH DELETE n')
    return graphdb


@pytest.mark.integration
def test_node_parameter_permutations(graphdb):
    """Test node representation."""
    result = yaml.load(open('tests/samples/node-parameter-permutations.yaml'))
    assert len(result) == 3
    result = graphdb.cypher.execute('MATCH (n) RETURN n')
    assert len(result) == 3  # All nodes
    result = graphdb.cypher.execute('MATCH (n)-[r]-(o) RETURN *')
    assert len(result) == 0  # No relationships
    result = graphdb.cypher.execute('MATCH (n:person) RETURN n')
    assert len(result) == 2  # 2 nodes with `person` label
    result = graphdb.cypher.execute('MATCH (n) WHERE exists(n.occupation) RETURN n')
    assert len(result) == 2  # 2 nodes with `occupation` property


@pytest.mark.integration
def test_relationship_structures(graphdb):
    """Test relationship representation."""
    result = yaml.load(open('tests/samples/relationships.yaml'))
    assert len(result) == 5
    result = graphdb.cypher.execute('MATCH (n) RETURN n')
    assert len(result) == 3  # 2 nodes
    result = graphdb.cypher.execute('MATCH (n)-[r]->(o) RETURN *')
    assert len(result) == 2  # 2 relationships
    result = graphdb.cypher.execute('MATCH (p)-[r:DIRECTED]->(m) RETURN p,r,m')
    assert len(result) == 1
    person, relationship, movie = first(result)
    assert person['name'] == 'Lana Wachowski'
    assert relationship.type == 'DIRECTED'
    assert movie['title'] == 'The Matrix'


@pytest.mark.integration
def test_complex_related_graph(graphdb):
    """Test loading a graph with multiple nodes & relationships."""
    result = yaml.load(open('tests/samples/nodes-and-relationships.yaml'))
    assert len(result) == 21
    result = graphdb.cypher.execute(
        'MATCH (p)-[r:DIRECTED]->(m{title:"The Matrix"}) RETURN p,r,m')
    assert len(result) == 1
    person, relationship, movie = first(result)
    assert person['name'] == 'Lana Wachowski'
    assert relationship.type == 'DIRECTED'
    assert movie['title'] == 'The Matrix'
