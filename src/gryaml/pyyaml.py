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


def node_constructor(loader, yaml_node):
    # type: (yaml.BaseLoader, yaml.Node) -> Node
    """Construct a Neo4j node from a YAML sequence."""
    return node(*(loader.construct_sequence(yaml_node, deep=True)))


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


def rel_constructor(loader, yaml_node):
    # type: (yaml.BaseLoader, yaml.Node) -> Relationship
    """Construct as Neo4j relationship from a YAML sequence."""
    return rel(*loader.construct_sequence(yaml_node, deep=True))


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
