"""Incomplete support for dump/load w/PyYAML."""

import yaml

from py2neo_compat import Node, Relationship, to_dict
# from py2neo.cypher.core import Record

from . import node, rel

node_tag = u'!gryaml.node'
rel_tag = u'!gryaml.rel'


def node_representer(dumper, data):
    # type: (yaml.BaseDumper, Node) -> yaml.SequenceNode
    """Represent a Neo4j node as YAML sequence node."""
    yaml_data = []

    if data.labels:
        yaml_data.append({'labels': list(data.labels)})

    properties = to_dict(data)
    if properties:
        yaml_data.append({'properties': properties})

    return dumper.represent_sequence(node_tag, yaml_data,
                                     flow_style=False)


yaml.add_multi_representer(Node, node_representer)


def node_constructor(loader, yaml_node):
    # type: (yaml.BaseLoader, yaml.Node) -> Node
    """Construct a Neo4j node from a YAML sequence."""
    return node(*(loader.construct_sequence(yaml_node, deep=True)))


yaml.add_constructor(node_tag, node_constructor)


def rel_representer(dumper, data):
    # type: (yaml.BaseDumper, Relationship) -> yaml.SequenceNode
    """Represent a Neo4j relationship as a YAML sequence node."""
    yaml_data = [
        data.start_node,
        data.type,
        data.end_node,
    ]

    properties = to_dict(data)
    if properties:
        yaml_data.append({'properties': properties})

    return dumper.represent_sequence(rel_tag, yaml_data, flow_style=False)


yaml.add_multi_representer(Relationship, rel_representer)


def rel_constructor(loader, yaml_node):
    # type: (yaml.BaseLoader, yaml.Node) -> Relationship
    """Construct as Neo4j relationship from a YAML sequence."""
    return rel(*loader.construct_sequence(yaml_node, deep=True))


yaml.add_constructor(rel_tag, rel_constructor)

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
