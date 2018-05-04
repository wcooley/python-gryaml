"""Support for dump/load w/PyYAML."""
from __future__ import absolute_import, print_function

from typing import Dict, List, Optional, Union

import yaml

from py2neo_compat import Node, Relationship, to_dict
# from py2neo.cypher.core import Record

from . import node, rel

node_tag = u'!gryaml.node'
rel_tag = u'!gryaml.rel'


def render_node(graph_node):
    # type: (Node) -> List[Dict[str, Union[List[str], Dict[str, str]]]]
    """Render a Neo4j node as a list

    A node is rendered as a 0-2 item list, with the following items:

    - # Single-key map, optional
        labels:  # List of labels
            - Label1
            - Label2
    - # Single-key map, optional
        properties:  # Mapping of Properties
            prop1: value1
            prop2: value2
    ."""
    data = []

    if graph_node.labels:
        data.append({'labels': list(graph_node.labels)})

    properties = to_dict(graph_node)
    if properties:
        data.append({'properties': properties})

    return data


def node_representer(dumper, graph_node):
    # type: (yaml.BaseDumper, Node) -> yaml.SequenceNode
    """Represent a Neo4j node as YAML sequence with ''!gryaml.node'' tag."""
    return dumper.represent_sequence(node_tag,
                                     render_node(graph_node),
                                     flow_style=False)


def node_representer_simple(dumper, graph_node):
    # type: (yaml.SafeDumper, Node) -> yaml.SequenceNode
    """Represent a Neo4j node as YAML list."""
    return dumper.represent_list(render_node(graph_node))


def node_constructor_simple(loader, yaml_node):
    # type: (yaml.SafeLoader, yaml.Node) -> List
    """Construct "node" with only primitive Python types."""
    return loader.construct_sequence(yaml_node, deep=True)


def node_constructor(loader, yaml_node):
    # type: (yaml.BaseLoader, yaml.Node) -> Node
    """Construct a Neo4j node from a YAML sequence."""
    return node(*node_constructor_simple(loader, yaml_node))


def render_relationship(graph_rel):
    # type: (Relationship) -> List
    """Render a Neo4j relationship as a list.

    Render relationships as a 3 or 4 item list:
    - Start node  # Node structure as above
    - Relationship Type  # str
    - End node  # Node structure as above
    - # Single-key map, optional
        properties:  # Mapping of properties
            prop1: value1
            prop2: value2
    """
    data = [
        graph_rel.start_node,
        graph_rel.type,
        graph_rel.end_node,
    ]

    properties = to_dict(graph_rel)
    if properties:
        data.append({'properties': properties})

    return data


def rel_representer(dumper, graph_rel):
    # type: (yaml.BaseDumper, Relationship) -> yaml.SequenceNode
    """Represent a Neo4j relationship as a YAML sequence node."""
    return dumper.represent_sequence(rel_tag,
                                     render_relationship(graph_rel),
                                     flow_style=False)


def rel_representer_simple(dumper, graph_rel):
    # type: (yaml.SafeDumper, Relationship) -> yaml.SequenceNode
    """Represent a Neo4j relationship as a YAML sequence. """
    return dumper.represent_list(render_relationship(graph_rel))


def rel_constructor_simple(loader, yaml_node):
    # type: (yaml.BaseLoader, yaml.Node) -> List
    """Construct a sequence from a tagged YAML sequence."""
    return loader.construct_sequence(yaml_node, deep=True)


def rel_constructor(loader, yaml_node):
    # type: (yaml.BaseLoader, yaml.Node) -> Relationship
    """Construct a Neo4j relationship from a tagged YAML sequence."""
    return rel(*rel_constructor_simple(loader, yaml_node))


def register(safe=False):
    # type: (Optional[bool]) -> None
    """Register representers & constructors for nodes & rels."""

    if safe:
        dumper = yaml.SafeDumper
        loader = yaml.SafeLoader
    else:
        dumper = yaml.Dumper
        loader = yaml.Loader

    yaml.add_multi_representer(Node, node_representer, Dumper=dumper)
    yaml.add_multi_representer(Relationship, rel_representer, Dumper=dumper)

    yaml.add_constructor(node_tag, node_constructor, Loader=loader)
    yaml.add_constructor(rel_tag, rel_constructor, Loader=loader)


def register_simple(safe=True):
    # type: () -> None
    """Register representers & constructors using only native YAML types."""

    if safe:
        dumper = yaml.SafeDumper
        loader = yaml.SafeLoader
    else:
        dumper = yaml.Dumper
        loader = yaml.Loader

    yaml.add_multi_representer(Node, node_representer_simple, Dumper=dumper)
    yaml.add_multi_representer(Relationship, rel_representer_simple,
                               Dumper=dumper)

    yaml.add_constructor(node_tag, node_constructor_simple, Loader=loader)

    yaml.add_constructor(rel_tag, rel_constructor_simple, Loader=loader)


def _unregister():
    # type: () -> None
    """Attempt to remove registered representers and constructors.

    This should probably only be used in testing, as manipulating the
    underlying dicts for the dumpers/loaders feels like an encapsulation
    violation, even though the attributes are not named according to the
    convention for private attributes. (Otherwise, why would the PyYAML author
    bother with the ``yaml.add_*`` methods?)
    """

    for loader in [yaml.BaseLoader, yaml.Loader, yaml.SafeLoader]:
        for tag in [node_tag, rel_tag]:
            loader.yaml_constructors.pop(tag, None)
            loader.yaml_multi_constructors.pop(tag, None)

    for dumper in [yaml.BaseDumper, yaml.Dumper, yaml.SafeDumper]:
        for cls in [Node, Relationship]:
            dumper.yaml_representers.pop(cls, None)
            dumper.yaml_multi_representers.pop(cls, None)


# py2neo and pyyaml have bugs that make this not straightforward:
# * py2neo assumes that a Record will only be compared to an iterable
# in `Record`'s `__eq__` method; it explicitly converts itself and "other"
# with `tuple()`, which fails if it is compared with `None`.
# * pyyaml has a bug in `representer.py`, function `ignore_aliases`,
# where it checks: `if data in [None, ()]:`, which performs an '=='
# comparison, not an 'is' comparison, which is correct for `None`.
#
# def record_representer(dumper, data):
#     """Represent."""
#     print('record rep called')
#     return dumper.represent_sequence(u'tag:yaml.org,2002:seq',
#         ['one', 'two'])
#         #[data[0], data[2], data[1]])
#
# yaml.add_representer(Record, record_representer)
