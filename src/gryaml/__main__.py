"""Load Neo4j nodes & relationships from YAML files."""

import argparse
import os
from typing import Any

import yaml
from py2neo_compat import Graph
from py2neo_compat.schema import drop_schema

import gryaml

gryaml.register()


def parse_args(args: list[str] | None = None) -> Any:
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


def __main__() -> None:
    config = parse_args()

    print(f'Using Neo4j database at {config.neo4j_uri}')

    graph = gryaml.connect(config.neo4j_uri)

    # Ensure at least a minimally functioning connection
    assert graph.neo4j_version

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

def cleanup_graph(graph: Graph) -> None:
    """Delete all entities & drop indexes & constraints."""
    drop_schema(graph)
    graph.delete_all()


if __name__ == '__main__':
    __main__()
