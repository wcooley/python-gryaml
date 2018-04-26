"""Tests for `gryaml` module."""
from __future__ import print_function

from textwrap import dedent

import pytest
import yaml
from boltons.iterutils import first

import gryaml
import py2neo_compat
from py2neo_compat import (
    foremost,
    Graph,
    Node,
    node,
    rel,
    Relationship,
)  # noqa: F401

py2neo_compat.monkey_patch_py2neo()


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
    result = match_all_nodes(graphdb)
    assert len(result) == 3  # All nodes
    result = match_all_nodes_and_rels(graphdb)
    assert len(result) == 0  # No relationships
    result = graphdb.cypher.execute('MATCH (n:person) RETURN n')
    assert len(result) == 2  # 2 nodes with `person` label
    result = graphdb.cypher.execute('MATCH (n) WHERE exists(n.occupation)'
                                    ' RETURN n')
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
    result = match_all_nodes(graphdb)
    assert len(result) == 3  # 3 nodes
    result = match_all_nodes_and_rels(graphdb)
    assert len(result) == 2  # 2 relationships
    result = graphdb.cypher.execute('MATCH (p)-[r:DIRECTED]->(m)'
                                    ' RETURN p,r,m')
    assert_lana_directed_matrix(result)


@pytest.mark.usefixtures('graphdb_offline')
@pytest.mark.unit
def test_complex_related_graph_offline():
    """Test graph with multiples nodes & relationships offline."""
    result = yaml.load(open('tests/samples/nodes-and-relationships.yaml'))
    assert len(result) == 21

    directed_rel = [(r.start_node, r, r.end_node)
                    for r in result
                    if isinstance(r, Relationship) and
                    r.type == 'DIRECTED' and
                    r.end_node['title'] == 'The Matrix']
    assert_lana_directed_matrix(directed_rel)


@pytest.mark.integration
def test_complex_related_graph(graphdb):
    """Test loading a graph with multiple nodes & relationships."""
    result = yaml.load(open('tests/samples/nodes-and-relationships.yaml'))
    assert len(result) == 21
    result = graphdb.cypher.execute("""
        MATCH (p)-[r:DIRECTED]->(m{title:"The Matrix"})
        RETURN p,r,m
        """)
    assert_lana_directed_matrix(result)


@pytest.fixture
def sample_simple_rel():
    # type: () -> Relationship
    """Produce a sample relationship."""
    # Awkward underscore avoids even more awkward quoting.
    return rel(node({'name': 'Babs_Jensen'}),
               'CHARACTER_IN',
               node({'name': 'Animal_House'}))


@pytest.mark.unit
def test_node_can_be_dumped(sample_simple_rel):
    # type: (Relationship) -> None
    """Test dump/represent Node."""
    sample_node = sample_simple_rel.start_node
    node_yaml = yaml.dump(sample_node, canonical=True)

    # import sys; print("\n---\n", node_yaml, file=sys.stderr)
    node_yaml = node_yaml.replace('!!python/unicode', '!!str')

    assert dedent("""
        ---
        !gryaml.node [
          !!map {
            ? !!str "properties"
            : !!map {
              ? !!str "name"
              : !!str "Babs_Jensen",
            },
          },
        ] """).strip() == node_yaml.strip()


@pytest.mark.unit
def test_node_subclass_can_be_dumped(sample_simple_rel):
    # type: (Relationship) -> None
    """Test dump/represent Node."""
    class MyNode(py2neo_compat.Node):
        @classmethod
        def new(cls, **kwargs):
            """Construct an abstract/unbound MyNode, properties only."""
            if py2neo_compat.py2neo_ver == 1:
                inst = cls(None)
                inst.set_properties(kwargs)
                return inst
            else:
                return cls(**kwargs)

    sample_node = MyNode.new(name='Babs_Jensen')
    node_yaml = yaml.dump(sample_node, canonical=True)

    node_yaml = node_yaml.replace('!!python/unicode', '!!str')
    # import sys; print("\n---\n", node_yaml, file=sys.stderr)

    assert dedent("""
        ---
        !gryaml.node [
          !!map {
            ? !!str "properties"
            : !!map {
              ? !!str "name"
              : !!str "Babs_Jensen",
            },
          },
        ] """).strip() == node_yaml.strip()


@pytest.mark.integration
def test_node_can_be_dumped_then_loaded(graphdb):
    # type: (Graph) -> None
    """Ensure a node can be YAML-dumped and then YAML-loaded."""
    assert 0 == len(match_all_nodes(graphdb))

    n = yaml.load("""
        !gryaml.node
        - labels: [person]
        - properties: {name: Babs_Jensen}
    """)

    babs_yaml1 = yaml.dump(n)

    r = match_all_nodes(graphdb)
    assert 1 == len(r)

    babs_yaml2 = yaml.dump(foremost(foremost(r)))

    assert babs_yaml1 == babs_yaml2

    graphdb.delete_all()
    assert 0 == len(match_all_nodes(graphdb))

    yaml.load(babs_yaml2)

    r = match_all_nodes(graphdb)
    assert 1 == len(r)

    babs_yaml3 = yaml.dump(foremost(foremost(r)))

    assert babs_yaml2 == babs_yaml3


@pytest.mark.unit
def test_rel_can_be_dumped(sample_simple_rel):
    # type: (Relationship) -> None
    """Ensure a relationship and nodes can be dumped."""
    rel_yaml = yaml.dump(sample_simple_rel, canonical=True)  # type: str

    # import sys; print("\n---\n",rel_yaml, "\n---\n", file=sys.stderr)

    # Py2.7 w/py2neo2 ends up with a unicode tag and quoted "name",
    # so manually rip those out to avoid having to use a regex
    rel_yaml = rel_yaml.replace('!!python/unicode', '!!str')

    assert dedent("""
        ---
        !gryaml.rel [
          !gryaml.node [
            !!map {
              ? !!str "properties"
              : !!map {
                ? !!str "name"
                : !!str "Babs_Jensen",
              },
            },
          ],
          !!str "CHARACTER_IN",
          !gryaml.node [
            !!map {
              ? !!str "properties"
              : !!map {
                ? !!str "name"
                : !!str "Animal_House",
              },
            },
          ],
        ]
    """).strip() == rel_yaml.strip()


@pytest.mark.integration
def test_rel_can_be_dumped_then_loaded(graphdb):
    # type: (Graph) -> None
    """Ensure a relationship and nodes can be dumped and loaded."""
    assert 0 == len(match_all_nodes_and_rels(graphdb))

    r = yaml.load("""
        - !gryaml.rel
          - !gryaml.node
            - labels:
                - person
            - properties:
                name: Babs Jensen
          - CHARACTER_IN
          - !gryaml.node
            - labels:
                - movie
            - properties:
                name: Animal House
    """)

    sample_yaml1 = yaml.dump(r)

    result = match_all_rels(graphdb)
    assert 1 == len(result)

    sample_yaml2 = yaml.dump(list(foremost(result)))

    assert sample_yaml1 == sample_yaml2

    graphdb.delete_all()

    assert 0 == len(match_all_nodes(graphdb))

    yaml.load(sample_yaml2)

    result = match_all_rels(graphdb)
    assert 1 == len(result)

    sample_yaml3 = yaml.dump(list(foremost(result)))

    assert sample_yaml2 == sample_yaml3


# Test helpers

def assert_lana_directed_matrix(result):
    """Assert given relationship & nodes."""
    assert len(result) == 1
    person, relationship, movie = first(result)
    assert person['name'] == 'Lana Wachowski'
    assert relationship.type == 'DIRECTED'
    assert movie['title'] == 'The Matrix'


def match_all_nodes(graphdb):
    """Query for all nodes."""
    return list(graphdb.cypher.execute('MATCH (n) RETURN n'))


def match_all_nodes_and_rels(graphdb):
    """Query for all nodes and relationships."""
    return list(graphdb.cypher.execute('MATCH (n1)-[r]->(n2)'
                                       ' RETURN n1, r, n2'))


def match_all_rels(graphdb):
    """Query for all relationships."""
    return list(graphdb.cypher.execute('MATCH ()-[r]->() RETURN r'))
