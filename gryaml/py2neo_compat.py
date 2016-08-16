"""Compatability layer for :mod:`py2neo` versions."""

from boltons.iterutils import first

try:
    from typing import Any, List, Mapping, Optional  # noqa
except ImportError:
    """Module :mod:`typing` not required for Py27-compatible type comments."""

import py2neo
if py2neo.__version__.startswith('1.6'):
    py2neo_ver = 1
elif py2neo.__version__.startswith('2.0'):
    py2neo_ver = 2
elif py2neo.__version__.startswith('3'):
    py2neo_ver = 3
    raise NotImplementedError("py2neo %d not yet supported" % py2neo_ver)
else:
    raise NotImplementedError("py2neo %d not supported" % py2neo.__version__)


if py2neo_ver == 1:
    from py2neo.neo4j import GraphDatabaseService as Graph  # noqa
    from py2neo.neo4j import CypherQuery, Node, Relationship  # noqa
    from py2neo import node as py2neo_node, rel as py2neo_rel  # noqa

elif py2neo_ver == 2:
    from py2neo import Graph, Node, Relationship  # noqa
    from py2neo import node as py2neo_node, rel as py2neo_rel  # noqa

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

    if graph:
        graphdb = graph
    else:
        graphdb = Graph(uri)

    return graphdb


def _not_none(o):
    # type: (Any) -> bool
    return o is not None


# Creating Nodes & Relationships in a database is only required for 1.6.
# Native _create_ can create multiple entities but this cannot

def py2neo16_create(entity):
    # type: (Py2NeoEntity) -> Py2NeoEntity
    # An empty 1.6 Node evaluates to False, so override the default way `first`
    # tests for falsity or we'll return None.
    return first(graphdb.create(entity), key=_not_none)


def py2neo20_create(entity):
    # type: (Py2NeoEntity) -> Py2NeoEntity
    result = entity
    try:
        if graphdb:
            result = first(graphdb.create(entity), key=_not_none)
    except NameError:
        pass

    return result

if py2neo_ver == 1:
    _create = py2neo16_create
elif py2neo_ver == 2:
    _create = py2neo20_create

del py2neo16_create, py2neo20_create


def py2neo16_node(labels=None, properties=None):
    # type: (List[str], Mapping[str, Any]) -> Node
    """Implement a Py2neo 2.0-compatible `node` factory.

    Version 1.6 did not support adding labels (which ordinarily would only be
    possible to add *after* node creation).
    """
    labels = labels or []
    properties = properties or {}

    new_node = _create(py2neo_node(properties))
    new_node.add_labels(*labels)

    return new_node


def py2neo20_node(labels=None, properties=None):
    # type: (List[str], Mapping[str, Any]) -> Node
    """Py2neo `node` factory.

    Requires a module-global `graphdb` connection.
    """
    labels = labels or []
    properties = properties or {}
    return _create(py2neo_node(*labels, **properties))


if py2neo_ver == 1:
    compat_node = py2neo16_node
elif py2neo_ver == 2:
    compat_node = py2neo20_node

del py2neo16_node, py2neo20_node


if py2neo_ver == 1:

    def _cypher_execute(graph, query, **params):
        # type: (Graph, str, **Mapping[str, Any]) -> Any
        return CypherQuery(graph, query).execute(**params)

    def _cypher_stream(graph, query, **params):
        # type: (Graph, str, **Mapping[str, Any]) -> Any
        return CypherQuery(graph, query).stream(**params)

elif py2neo_ver == 2:

    def _cypher_execute(graph, query, **params):
        # type: (Graph, str, **Mapping[str, Any]) -> Any
        return graph.cypher.execute(query, **params)

    def _cypher_stream(graph, query, **params):
        # type: (Graph, str, **Mapping[str, Any]) -> Any
        return graph.cypher.stream(query, **params)


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
    return compat_node(labels, properties)


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
    results = first(_create(path), key=_not_none)
    return results
