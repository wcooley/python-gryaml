"""Incomplete support for dump/load w/PyYAML."""

import yaml

from .py2neo_compat import Node, Relationship
# from py2neo.cypher.core import Record

from . import node, rel

# Future improvement:
# Custom tags & representers/constructors to make both dump and load work
#
node_tag = u'!gryaml.node'
rel_tag = u'!gryaml.rel'


def node_representer(dumper, data):
    """Represent."""
    yaml_data = [
        {'labels': list(data.labels)},
        {'properties': dict(data.properties)},
    ]
    return dumper.represent_sequence(node_tag, yaml_data,
                                     flow_style=False)


yaml.add_representer(Node, node_representer)


def node_constructor(loader, yaml_node):
    """Construct."""
    return node(*(loader.construct_sequence(yaml_node, deep=True)))


yaml.add_constructor(node_tag, node_constructor)


def rel_representer(dumper, data):
    """Represent."""
    yaml_data = [
        data.start_node,
        data.type,
        data.end_node,
        {'properties': dict(data.properties)},
    ]
    return dumper.represent_sequence(rel_tag, yaml_data, flow_style=False)


yaml.add_representer(Relationship, rel_representer)


def rel_constructor(loader, yaml_node):
    """Construct."""
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
