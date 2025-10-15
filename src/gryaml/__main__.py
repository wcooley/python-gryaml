"""Load Neo4j nodes & relationships from YAML files."""

import argparse
import os

import yaml

try:
    from typing import Any, Iterator, List, Optional, Tuple  # noqa: F401
    from py2neo_compat import Graph  # noqa: F401
except ImportError:
    """Module :mod:`typing` not required for Py27-compatible type comments."""

from py2neo_compat.schema import drop_schema

import gryaml
gryaml.register()


def parse_args(args=None):
    # type: (Optional[List[str]]) -> Any
    """Parse command-line arguments."""
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

    return parser.parse_args(args)


def __main__():  # noqa: N802
    # type: () -> None
    config = parse_args()

    print('Using Neo4j database at {}'.format(config.neo4j_uri))

    graph = gryaml.connect(config.neo4j_uri)

    # Ensure at least a minimally functioning connection
    graph.neo4j_version

    # import sys, IPython; IPython.embed(); sys.exit()
    if config.drop:
        print('Dropping database...')
        cleanup_graph(graph)

    if config.yaml_files:
        print('Loading YAML files...')

    for yaml_file in config.yaml_files:
        print(yaml_file)
        with open(yaml_file) as stream:
            yaml.load(stream, yaml.Loader)

def cleanup_graph(graph):
    # type: (Graph) -> None
    """Delete all entities & drop indexes & constraints."""
    drop_schema(graph)
    graph.delete_all()


if __name__ == '__main__':
    __main__()
