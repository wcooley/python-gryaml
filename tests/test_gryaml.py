"""Tests for `gryaml` module."""

import os

import pytest
import yaml
from boltons.iterutils import first

import gryaml
import gryaml.py2neo_compat
from gryaml.py2neo_compat import Node, Relationship


@pytest.fixture
def graphdb():
    """Fixture connecting to graphdb."""
    if 'NEO4J_URI' not in os.environ:
        pytest.skip('Need NEO4J_URI environment variable set')
    graphdb = gryaml.connect(uri=os.environ['NEO4J_URI'])
    graphdb.cypher.execute('MATCH (n) DETACH DELETE n')
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


@pytest.mark.usefixtures('graphdb_offline')
@pytest.mark.unit
def test_node_parameter_permutation_offline():
    """Test nodes offline."""
    result = yaml.load(open('tests/samples/node-parameter-permutations.yaml'))

    # All nodes
    assert len(result) == 3

    # No relationships
    assert {type(n) for n in result} == {type(Node())}

    # 2 nodes with 'person' label
    assert len([n for n in result if n.labels]) == 2
    assert set(first(n.labels) for n in result if n.labels) == {'person'}

    # 2 nodes with `occupation` property
    occupations = [n['occupation'] for n in result if n['occupation']]
    assert len(occupations) == 2
    assert set(occupations) == {'Comedian', 'Game Show Host'}


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

@pytest.mark.usefixtures('graphdb_offline')
@pytest.mark.unit
def test_relationship_structures_offline():
    """Test relationship representations offline."""
    result = yaml.load(open('tests/samples/relationships.yaml'))
    assert len(result) == 5
    nodes = [n for n in result if isinstance(n, Node)]
    assert len(nodes) == 3  # 3 nodes
    rels = [r for r in result if isinstance(r, Relationship)]
    assert len(rels) == 2  # 2 relationships

    directed_rel = [(r.start_node, r, r.end_node)
                    for r in result
                    if isinstance(r, Relationship) and r.type == 'DIRECTED']
    assert_lana_directed_matrix(directed_rel)


@pytest.mark.integration
def test_relationship_structures(graphdb):
    """Test relationship representation."""
    result = yaml.load(open('tests/samples/relationships.yaml'))
    assert len(result) == 5
    result = graphdb.cypher.execute('MATCH (n) RETURN n')
    assert len(result) == 3  # 3 nodes
    result = graphdb.cypher.execute('MATCH (n)-[r]->(o) RETURN *')
    assert len(result) == 2  # 2 relationships
    result = graphdb.cypher.execute('MATCH (p)-[r:DIRECTED]->(m) RETURN p,r,m')
    assert_lana_directed_matrix(result)


@pytest.mark.usefixtures('graphdb_offline')
@pytest.mark.unit
def test_complex_related_graph_offline():
    """Test graph with multiples nodes & relationships offline."""
    result = yaml.load(open('tests/samples/nodes-and-relationships.yaml'))
    assert len(result) == 21

    directed_rel = [(r.start_node, r, r.end_node)
                    for r in result
                    if isinstance(r, Relationship)
                    and r.type == 'DIRECTED'
                    and r.end_node['title'] == 'The Matrix']
    assert_lana_directed_matrix(directed_rel)


@pytest.mark.integration
def test_complex_related_graph(graphdb):
    """Test loading a graph with multiple nodes & relationships."""
    result = yaml.load(open('tests/samples/nodes-and-relationships.yaml'))
    assert len(result) == 21
    result = graphdb.cypher.execute(
        'MATCH (p)-[r:DIRECTED]->(m{title:"The Matrix"}) RETURN p,r,m')
    assert_lana_directed_matrix(result)


def assert_lana_directed_matrix(result):
    """Assert given relationship & nodes."""
    assert len(result) == 1
    person, relationship, movie = first(result)
    assert person['name'] == 'Lana Wachowski'
    assert relationship.type == 'DIRECTED'
    assert movie['title'] == 'The Matrix'
