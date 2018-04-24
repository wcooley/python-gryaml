"""Compatability layer for :mod:`py2neo` versions."""
from __future__ import absolute_import


from boltons.iterutils import first

try:
    from typing import Any, List, Mapping, Optional  # noqa
except ImportError:
    """Module :mod:`typing` not required for Py27-compatible type comments."""

import py2neo_compat
py2neo_compat.monkey_patch_py2neo()

from py2neo_compat import (
    Graph, Node, Relationship, py2neo_ver, create_node, foremost,
    rel as py2neo_rel
)


try:
    from typing import TypeVar
    Py2NeoEntity = TypeVar('Py2NeoEntity', Node, Relationship)
except ImportError:
    pass

# Avoid overwriting on reload
try:
    graphdb
except NameError:
    graphdb = None  # type: Graph


def connect(uri=None, graph=None):
    # type: (Optional[str], Optional[Graph]) -> Graph
    """Instantiate a module-level graph database connection."""
    global graphdb

    if graph is not None:
        graphdb = graph
    else:
        graphdb = Graph(uri)

    return graphdb


def is_arg_map(argname, mapping):
    # type: (str, Mapping[str, Mapping]) -> bool
    """Determine if p is an "arg map".

    I.e., a singleton mapping with key `argname` with the actual
    parameters/properties as the value:

        { 'properties': {
            'color': 'blue',
            'size': 'medium'
            }
        }

        { 'labels': ['shirt', 'clothing'] }
    """
    return argname in mapping and len(mapping) == 1


def is_properties_map(mapping):
    # type: (Mapping[str, Any]) -> bool
    """Determine if `mapping` is an "arg map" for properties."""
    return is_arg_map('properties', mapping)


def is_label_map(mapping):
    # type: (Mapping[str, Any]) -> bool
    """Determine if `mapping` is an "arg map" for labels."""
    return is_arg_map('labels', mapping)


def node(*args):
    # type: (*Mapping[str,Any]) -> Node
    """PyYAML wrapper constructor for creating nodes.

    This allows the YAML node to have 'labels' and 'properties' instead of
    'args' and 'kwargs', at the expense of having to do a little massaging of
    the parameters (which come in as positional variables with a single-key
    mapping).

    >>> import yaml
    >>> result = yaml.load('''
    !!python/object/apply:gryaml.node2
        - labels:
            - 'person'
        - properties:
            name: 'Bob Newhart'
            occupation: 'Comedian'
    ''')
    >>> isinstance(result, Node)
    """
    labels = first(arg['labels']
                   for arg in args if is_label_map(arg)) or []
    properties = first(arg['properties']
                       for arg in args if is_properties_map(arg)) or {}
    return create_node(graph=graphdb, labels=labels, properties=properties)


def resolve_rel_properties(properties=None):
    # type: (Mapping) -> Mapping
    """Extract properties from rel structure.

    This supports the properties of a rel being either an "arg map" with key
    'properties' or just a mapping.

        -
            - properties:
                color: blue
                size: medium
    or:

        - color: blue
          size: medium

    While the latter is more compact, the former is more consistent with how
    nodes are represented.
    """
    properties = properties or {}  # Ensure not default `None`
    # Support properties being either the value of a single-key mapping with
    # key 'properties' or directly
    properties = properties['properties'] \
        if is_properties_map(properties) \
        else properties

    return properties


def rel(head, reltype, tail, properties=None):
    # type: (Node, str, Node, Mapping) -> Relationship
    """Create relationships."""
    properties = resolve_rel_properties(properties)
    path = py2neo_rel(head, reltype, tail, **properties)

    # Offline/abstract creation
    return path if graphdb is None \
        else foremost(graphdb.create(path))
