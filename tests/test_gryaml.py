"""Tests for `gryaml` module."""
from __future__ import print_function

from textwrap import dedent

from typing import Callable, List, Union

import pytest
import yaml
from boltons.iterutils import first

import gryaml
import py2neo_compat
# noinspection PyProtectedMember
from gryaml.pyyaml import _unregister as gryaml_unregister
from py2neo_compat import (
    foremost,
    Graph,
    Node,
    node,
    rel,
    Relationship,
)  # noqa: F401

py2neo_compat.monkey_patch_py2neo()


@pytest.fixture(autouse=True)
def unregister_gryaml():
    """Ensure every test explicitly registers."""
    gryaml_unregister()


@pytest.mark.usefixtures('graphdb_offline')
@pytest.mark.unit
def test_node_parameter_permutation_offline(sample_yaml):
    # type: (Callable[[str], str]) -> None
    """Test nodes offline."""
    gryaml.register()

    result = yaml.load(sample_yaml('node-parameter-permutations'))

    # All nodes
    assert 3 == len(result)

    # No relationships
    assert {type(Node())} == {type(n) for n in result}

    # 2 nodes with 'person' label
    assert 2 == len([n for n in result if n.labels])
    assert {'person'} == set(first(n.labels) for n in result if n.labels)

    # 2 nodes with `occupation` property
    occupations = [n['occupation'] for n in result if n['occupation']]
    assert 2 == len(occupations)
    assert {'Comedian', 'Game Show Host'} == set(occupations)


@pytest.mark.integration
def test_node_parameter_permutations(graphdb, sample_yaml):
    # type: (Graph, Callable[[str], str]) -> None
    """Test node representation."""
    gryaml.register()

    result = yaml.load(sample_yaml('node-parameter-permutations'))
    assert 3 == len(result)
    result = match_all_nodes(graphdb)
    assert 3 == len(result)  # All nodes
    result = match_all_nodes_and_rels(graphdb)
    assert 0 == len(result)  # No relationships
    result = graphdb.cypher.execute('MATCH (n:person) RETURN n')
    assert 2 == len(result)  # 2 nodes with `person` label
    result = graphdb.cypher.execute('MATCH (n) WHERE exists(n.occupation)'
                                    ' RETURN n')
    assert 2 == len(result)  # 2 nodes with `occupation` property


@pytest.mark.usefixtures('graphdb_offline')
@pytest.mark.unit
def test_relationship_structures_offline(sample_yaml):
    # type: (Callable[[str], str]) -> None
    """Test relationship representations offline."""
    gryaml.register()

    result = yaml.load(sample_yaml('relationships'))
    assert 5 == len(result)
    nodes = [n for n in result if isinstance(n, Node)]
    assert 3 == len(nodes)  # 3 nodes
    rels = [r for r in result if isinstance(r, Relationship)]
    assert 2 == len(rels)  # 2 relationships

    directed_rel = [(r.start_node, r, r.end_node)
                    for r in result
                    if isinstance(r, Relationship) and r.type == 'DIRECTED']
    assert_lana_directed_matrix(directed_rel)


@pytest.mark.integration
def test_relationship_structures(graphdb, sample_yaml):
    # type: (Graph, Callable[[str], str]) -> None
    """Test relationship representation."""
    gryaml.register()

    result = yaml.load(sample_yaml('relationships'))
    assert 5 == len(result)
    result = match_all_nodes(graphdb)
    assert 3 == len(result)  # 3 nodes
    result = match_all_nodes_and_rels(graphdb)
    assert 2 == len(result)  # 2 relationships
    result = graphdb.cypher.execute('MATCH (p)-[r:DIRECTED]->(m)'
                                    ' RETURN p,r,m')
    assert_lana_directed_matrix(result)


@pytest.mark.usefixtures('graphdb_offline')
@pytest.mark.unit
def test_complex_related_graph_offline(sample_yaml):
    # type: (Callable[[str], str]) -> None
    """Test graph with multiples nodes & relationships offline."""
    gryaml.register()

    result = yaml.load(sample_yaml('nodes-and-relationships'))
    assert 21 == len(result)

    directed_rel = [(r.start_node, r, r.end_node)
                    for r in result
                    if isinstance(r, Relationship) and
                    r.type == 'DIRECTED' and
                    r.end_node['title'] == 'The Matrix']
    assert_lana_directed_matrix(directed_rel)


@pytest.mark.integration
def test_complex_related_graph(graphdb, sample_yaml):
    # type: (Graph, Callable[[str], str]) -> None
    """Test loading a graph with multiple nodes & relationships."""
    gryaml.register()

    result = yaml.load(sample_yaml('nodes-and-relationships'))
    assert 21 == len(result)
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


@pytest.mark.integration
def test_node_can_be_loaded_and_created(graphdb):
    # type: (Relationship) -> None
    """Test loading a single node, creating in the DB and returning it."""
    gryaml.register()

    sample_yaml = """
        !gryaml.node
          - properties:
              name: Babs_Jensen
          - labels:
            - person
        """

    node_loaded = yaml.load(sample_yaml)
    node_found = foremost(match_all_nodes(graphdb))

    assert node_loaded == node_found

    node_data = yaml.load(sample_yaml.replace('!gryaml.node', ''))

    assert node_data[0]['properties'] == py2neo_compat.to_dict(node_loaded)
    assert node_data[1]['labels'] == list(node_loaded.labels)


@pytest.mark.unit
def test_node_can_be_loaded_simple():
    # type: () -> None
    """Test loading a single node with "simple" representation.

    The "simple" representation should return the same structure that would
    be created if the '!gryaml.node' tag were absent or the implicit type.
    """
    gryaml.register_simple()

    sample_yaml = """
        !gryaml.node
          - properties:
              name: Babs_Jensen
          - labels:
            - person
        """

    node_loaded = yaml.safe_load(sample_yaml)

    node_data = yaml.load(sample_yaml.replace('!gryaml.node', ''))
    assert node_data == node_loaded

    node_data = yaml.load(sample_yaml.replace('!gryaml.node', '!!seq'))
    assert node_data == node_loaded


@pytest.mark.unit
def test_node_can_be_dumped(sample_simple_rel):
    # type: (Relationship) -> None
    """Test dump/represent Node."""
    gryaml.register()

    sample_node = sample_simple_rel.start_node
    node_yaml = yaml.dump(sample_node, canonical=True)

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
def test_node_subclass_can_be_dumped():
    # type: (Relationship) -> None
    """Test dump/represent Node."""
    gryaml.register()

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
def test_node_can_be_dumped_simple(sample_simple_rel):
    # type: (Relationship) -> None
    """Test dump/represent Node."""
    gryaml.register_simple()
    # gryaml.register_simple(safe=False)

    sample_node = sample_simple_rel.start_node
    node_yaml = yaml.safe_dump(sample_node, canonical=True)

    node_yaml = node_yaml.replace('!!python/unicode', '!!str')

    expected_yaml = dedent("""
        ---
        !!seq [
          !!map {
            ? !!str "properties"
            : !!map {
              ? !!str "name"
              : !!str "Babs_Jensen",
            },
          },
        ]""").strip()

    assert expected_yaml == node_yaml.strip()


@pytest.mark.integration
def test_node_can_be_dumped_then_loaded(graphdb):
    # type: (Graph) -> None
    """Ensure a node can be YAML-dumped and then YAML-loaded."""
    gryaml.register()

    assert 0 == len(match_all_nodes(graphdb))

    n = yaml.load("""
        !gryaml.node
        - labels: [person]
        - properties: {name: Babs_Jensen}
    """)

    babs_yaml1 = yaml.dump(n)

    r = match_all_nodes(graphdb)
    assert 1 == len(r)

    babs_yaml2 = yaml.dump(foremost(r))

    assert babs_yaml1 == babs_yaml2

    graphdb.delete_all()
    assert 0 == len(match_all_nodes(graphdb))

    yaml.load(babs_yaml2)

    r = match_all_nodes(graphdb)
    assert 1 == len(r)

    babs_yaml3 = yaml.dump(foremost(r))

    assert babs_yaml2 == babs_yaml3


@pytest.mark.unit
def test_rel_can_be_dumped(sample_simple_rel):
    # type: (Relationship) -> None
    """Ensure a relationship and nodes can be dumped."""
    gryaml.register()

    rel_yaml = yaml.dump(sample_simple_rel, canonical=True)  # type: str

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


@pytest.mark.unit
def test_rel_can_be_dumped_simple(sample_simple_rel):
    # type: (Relationship) -> None
    """Ensure a relationship and nodes can be dumped."""
    gryaml.register_simple()

    rel_yaml = yaml.safe_dump(sample_simple_rel, canonical=True)  # type: str

    # Py2.7 w/py2neo2 ends up with a unicode tag and quoted "name",
    # so manually rip those out to avoid having to use a regex
    rel_yaml = rel_yaml.replace('!!python/unicode', '!!str')

    assert dedent("""
        ---
        !!seq [
          !!seq [
            !!map {
              ? !!str "properties"
              : !!map {
                ? !!str "name"
                : !!str "Babs_Jensen",
              },
            },
          ],
          !!str "CHARACTER_IN",
          !!seq [
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
    gryaml.register()

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

    sample_yaml2 = yaml.dump(result)

    assert sample_yaml1 == sample_yaml2

    graphdb.delete_all()

    assert 0 == len(match_all_nodes(graphdb))

    yaml.load(sample_yaml2)

    result = match_all_rels(graphdb)
    assert 1 == len(result)

    sample_yaml3 = yaml.dump(result)

    assert sample_yaml2 == sample_yaml3


@pytest.mark.skip_py2neo1
@pytest.mark.todo
@pytest.mark.integration
def test_representers(graphdb):
    # type: (Graph) -> None
    # gryaml.register_simple()
    gryaml.register()

    # language=cypher
    graphdb.cypher.execute("""
        CREATE (cloudAtlas:Movie { title:"Cloud Atlas",released:2012 })
        CREATE (forrestGump:Movie { title:"Forrest Gump",released:1994 })
        CREATE (robert:Person { name:"Robert Zemeckis", born:1951 })
        CREATE (tom:Person { name:"Tom Hanks", born:1956 })
        CREATE (tom)-[:ACTED_IN { roles: ["Forrest"]}]->(forrestGump)
        CREATE (tom)-[:ACTED_IN { roles: ['Zachry']}]->(cloudAtlas)
        CREATE (robert)-[:DIRECTED]->(forrestGump)""")

    expected = dedent("""
        - !gryaml.rel
          - &id001 !gryaml.node
            - labels: [Person]
            - properties: {born: 1956, name: Tom Hanks}
          - ACTED_IN
          - !gryaml.node
            - labels: [Movie]
            - properties: {released: 2012, title: Cloud Atlas}
          - properties:
              roles: [Zachry]
        - !gryaml.rel
          - *id001
          - ACTED_IN
          - &id002 !gryaml.node
            - labels: [Movie]
            - properties: {released: 1994, title: Forrest Gump}
          - properties:
              roles: [Forrest]
        - !gryaml.rel
          - !gryaml.node
            - labels: [Person]
            - properties: {born: 1951, name: Robert Zemeckis}
          - DIRECTED
          - *id002
    """).lstrip()
    all_graph = match_all_rels(graphdb)
    import sys, pprint; print(pprint.pformat(all_graph), file=sys.stderr)
    all_graph_yaml = yaml.dump(all_graph, canonical=False).lstrip()
    # import sys; print(all_graph_yaml, file=sys.stderr)
    # assert all_graph_yaml == ''

    # This, unfortunately, does not work consistently, due to result ordering
    # being non-deterministic and anchors/aliases being different:
    # assert expected == all_graph_yaml

    for s in ['!gryaml.rel', '!gryaml.node', 'labels', 'properties', '\n']:
        assert expected.count(s) == all_graph_yaml.count(s)

    all_graph_base = yaml.load(all_graph_yaml, Loader=yaml.BaseLoader)
    expected_base = yaml.load(expected, Loader=yaml.BaseLoader)

    assert expected_base == all_graph_base
    # what does the base data look like?
    # assert expected_base == []


@pytest.mark.todo
@pytest.mark.skip_py2neo1
@pytest.mark.integration
def test_quoting(graphdb):
    # type: (Graph) -> None
    """Test that quoting of labels, types, etc is as expected."""
    gryaml.register()

    expected_yaml = dedent("""
        - !gryaml.rel
          - !gryaml.node
            - labels: [Also Special Person]
            - properties: {Real Name: Alice B. Toklas}
          - IN LOVE WITH
          - !gryaml.node
            - labels: [Special Person]
            - properties: {Pet Name: Gertie}
        """).lstrip()

    # language=cypher
    graphdb.cypher.execute("""
        CREATE (gertie:`Special Person` {`Pet Name`: 'Gertie'})
        CREATE (alice:`Also Special Person` {`Real Name`: 'Alice B. Toklas'})
        CREATE (alice)-[ilw:`IN LOVE WITH`]->(gertie) RETURN *;
    """)

    results = [list(r) for r in graphdb.match()]
    yaml_serial = yaml.dump(results, canonical=True)
    yaml_serial = yaml_serial.lstrip().replace('!!python/unicode', '!!str')
    assert expected_yaml == yaml_serial

    graphdb.cypher.execute('MATCH (n) DETACH DELETE n')
    assert 0 == len(list(graphdb.match()))

    loaded_entities = yaml.load(yaml_serial)
    queried_entities = [list(r) for r in graphdb.match()]

    assert loaded_entities
    assert [None] != loaded_entities
    assert queried_entities

    # assert loaded_entities == queried_entities

    assert expected_yaml == yaml.dump(loaded_entities).lstrip()
    assert expected_yaml == yaml.dump(queried_entities).lstrip()


# Test helpers

def assert_lana_directed_matrix(result):
    # type: (List[Union[Node, Relationship]]) -> None
    """Assert given relationship & nodes."""
    assert 1 == len(result)
    person, relationship, movie = first(result)
    assert 'Lana Wachowski' == person['name']
    assert 'DIRECTED' == relationship.type
    assert 'The Matrix' == movie['title']


def match_all_nodes(graphdb):
    # type: (Graph) -> List[Node]
    """Query for all nodes."""
    return [foremost(r) for r in graphdb.cypher.execute('MATCH (n) RETURN n')]


def match_all_nodes_and_rels(graphdb):
    # type: (Graph) -> List[List[Node, Relationship, Node]]
    """Query for all nodes and relationships."""
    return [list(r)
            for r in graphdb.cypher.execute('MATCH (n1)-[r]->(n2)'
                                            ' RETURN n1, r, n2')]


def match_all_rels(graphdb):
    # type: (Graph) -> List[Node]
    """Query for all relationships."""
    return [foremost(r)
            for r in graphdb.cypher.execute('MATCH ()-[r]->() RETURN r')]


def test_helpers(graphdb):
    # type: (Graph) -> None
    """Ensure that test helpers work as expected."""
    r = graphdb.cypher.execute("""
        CREATE (cloudAtlas:Movie { title:"Cloud Atlas",released:2012 })
        CREATE (forrestGump:Movie { title:"Forrest Gump",released:1994 })
        CREATE (robert:Person { name:"Robert Zemeckis", born:1951 })
        CREATE (tom:Person { name:"Tom Hanks", born:1956 })
        CREATE (tom)-[r1:ACTED_IN { roles: ["Forrest"]}]->(forrestGump)
        CREATE (tom)-[r2:ACTED_IN { roles: ['Zachry']}]->(cloudAtlas)
        CREATE (robert)-[r3:DIRECTED]->(forrestGump)
        WITH [r1, r2, r3] as rs
        UNWIND rs as rel
        RETURN rel
        """)

    r = list(r)
    assert 3 == len(r)
    # assert not r

    all_rels = match_all_rels(graphdb)
    assert 3 == len(all_rels)
    for rel_ in all_rels:
        assert isinstance(rel_, Relationship)
        assert rel_.type in {'ACTED_IN', 'DIRECTED'}

    all_nodes = match_all_nodes(graphdb)
    assert 4 == len(all_nodes)
    for node_ in all_nodes:
        assert isinstance(node_, Node)
        assert tuple(node_.labels) in {('Movie',), ('Person',)}

    all_nodes_and_rels = match_all_nodes_and_rels(graphdb)
    assert 3 == len(all_nodes_and_rels)
    for start_node, rel_, end_node in all_nodes_and_rels:
        assert isinstance(start_node, Node)
        assert isinstance(end_node, Node)
        assert isinstance(rel_, Relationship)
        assert start_node == rel_.start_node
        assert end_node == rel_.end_node
