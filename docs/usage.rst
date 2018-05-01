========
Usage
========


Nodes & relationships can be created automatically in a Neo4j database upon
load using ``!gryaml.node`` or ``!gryaml.rel`` YAML
`local tag <http://yaml.org/spec/1.1/#local%20tag/>`_.

#. A connection to the graph database needs to be established using
   ``gryaml.connect(uri=URI)`` or ``gryaml.connect(graph=py2neo.Graph(...))``.
   This stores the graph handle in the global module namespace because it is not
   possible to pass in a handle to the constructors otherwise.

   ::

       import gryaml

       gryaml.connect('http://localhost:7474')

#. Import :mod:`pyyaml` and load the data:

   ::

        import yaml
        yaml.load("""
        - &node-foo !!python/object/apply:gryaml.node
          - labels:
            - 'Fooer'
          - properties:
            prop1: 'flim'
        - &node-bar !!python/object/apply:gryaml.node
          - labels:
            - 'Barer'
          - properties:
            prop1: 'flam'
        - !!python/object/apply:gryaml.rel
          - *node-foo
          - 'RELATES_TO'
          - *node-bar
          - properties:
            bletch: 'xyzzy'
        """)


   The ``&node-x`` are YAML `anchors <http://yaml.org/spec/1.1/#anchor/syntax>`_
   and ``*node-x`` are `aliases <http://yaml.org/spec/1.1/#alias/syntax>`_.

   See the ``tests/samples`` directory for other data examples.
