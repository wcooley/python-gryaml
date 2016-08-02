import os
import sys

import yaml
from py2neo import Graph

import gryaml

def __main__(argv=sys.argv):
    if '--help' in argv or len(argv) < 2:
        print('Usage: gryaml-load [neo4j_uri] file*')
        print('Environment variable "NEO4J_URI" may also be used')
        sys.exit()

    if len(argv) == 2 and os.environ.get('NEO4J_URI', None):
        neo4j_uri = os.environ['NEO4J_URI']
        yaml_input = argv[1:]
    else:
        neo4j_uri = argv[1]
        yaml_input = argv[2:]

    print('Using Neo4j database at {}'.format(neo4j_uri))
    graph = Graph(neo4j_uri)

    # Ensure at least a minimally functioning conection
    graph.neo4j_version

    print('Dropping database...')
    cleanup_graph(graph)

    gryaml.connect(neo4j_uri)

    print('Loading YAML files...')

    for yaml_file in yaml_input:
        print(yaml_file)
        with open(yaml_file) as stream:
            yaml.load(stream)

def schema_constraints(graph):
    # type: (Graph) -> (str, List[str], str)
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
    # type: (py2neo.Graph) -> (str, List[str])
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
    # type: (py2neo.Graph) -> None
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
