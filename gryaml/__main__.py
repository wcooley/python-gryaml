"""Load Neo4j nodes & relationships from YAML files."""

import argparse
import os
import sys

import yaml
from py2neo import Graph

try:
    from typing import Any, Iterator, Tuple  # noqa
    from .py2neo_compat import Graph  # noqa
except ImportError:
    """Module :mod:`typing` not required for Py27-compatible type comments."""

import gryaml


def parse_args(args=None):
    # type: (List) -> Any
    parser = argparse.ArgumentParser(description=__doc__)

    neo4j_uri_env = os.environ.get('NEO4J_URI', None)
    parser.add_argument('--neo4j-uri', action='store',
                        default=neo4j_uri_env,  # toggle req based on env var
                        required=not bool(neo4j_uri_env),
                        help='URI for Neo4j; environment variable'
                             ' "NEO4J_URI" may also be used.')
    parser.add_argument('--drop', action='store_true',
                        help='Drop database before loading.')
    parser.add_argument('yaml_files', nargs='*')

    args = parser.parse_args(args)
    return args


def __main__():
    # type: () -> None
    config = parse_args()

    print('Using Neo4j database at {}'.format(config.neo4j_uri))
    graph = Graph(config.neo4j_uri)

    # Ensure at least a minimally functioning connection
    graph.neo4j_version

    # import sys, IPython; IPython.embed(); sys.exit()
    if config.drop:
        print('Dropping database...')
        cleanup_graph(graph)

    gryaml.connect(config.neo4j_uri)

    if config.yaml_files:
        print('Loading YAML files...')

    for yaml_file in config.yaml_files:
        print(yaml_file)
        with open(yaml_file) as stream:
            yaml.load(stream)


def schema_constraints(graph):
    # type: (Graph) -> Iterator[Tuple[str, List[str], str]]
    """Query iterable list of *all* schema constraints.

    This works around the fact that, in Neo4j 2.3 and :mod:`py2neo` 2.0.8 at
    least, `graph.node_labels` only returns labels used by extant nodes, whereas
    previously it returned all labels, which are needed for clearing the
    constrain schema by iterating over the labels.
    """
    constraint_resource = graph.resource.resolve('schema/constraint')

    # return constraint_resource.get().content
    return ((c['label'], c['property_keys'], c['type'])
            for c in constraint_resource.get().content)


def schema_indexes(graph):
    # type: (Graph) -> List[Tuple[str, List[str]]]
    """Query iterable list of *all* schema indexes.

    This works around the fact that, in Neo4j 2.3 and :mod:`py2neo` 2.0.8 at
    least, `graph.node_labels` only returns labels used by extant nodes, whereas
    previously it returned all labels, which are needed for clearing the
    constrain schema by iterating over the labels.
    """
    index_resource = graph.resource.resolve('schema/index')

    return [(n['label'], n['property_keys']) for n in
            index_resource.get().content]


def cleanup_graph(graph):
    # type: (Graph) -> None
    """Delete all entities & drop indexes & constraints."""
    constraint_dispatch = {
        'UNIQUENESS': graph.schema.drop_uniqueness_constraint,
    }

    for label, property_keys, type in schema_constraints(graph):
        constraint_dispatch[type](label, property_keys)

    for label, property_keys in schema_indexes(graph):
        graph.schema.drop_index(label, property_keys)

    graph.delete_all()


if __name__ == '__main__':
    __main__()
