=============================
gryaml
=============================


.. image:: https://img.shields.io/pypi/v/gryaml.svg
        :target: https://pypi.python.org/pypi/gryaml

..
    .. image:: https://travis-ci.org/wcooley/python-gryaml.png?branch=master
        :target: https://travis-ci.org/wcooley/python-gryaml

    .. image:: https://pypip.in/d/gryaml/badge.png
        :target: https://pypi.python.org/pypi/gryaml



Represent Neo4j graph data as YAML.


Features
--------

* Creates nodes and relationships in a Neo4j graph database from YAML using
  PyYAML-specific tags.
* Operates at a whole-file level, as it uses custom YAML tags to deserialize
  the data to live objects.
* Developed for loading data for integration testing.
* Requires a running Neo4j instance and instantiates actual database entities,
  rather than just generating abstract/unbound ``py2neo.Node`` and
  ``py2neo.Relationship`` objects. This is due to ``py2neo`` version
  1.6 not supporting node labels with abstract nodes. This might be changed if
  we are able to migrate off of 1.6 in the near future.

Versions
--------

Python
    Tested with both Python 2.7 and 3.6.
Neo4j
    Should work with anything >= 2.0. Tested with 3.3.5. Running the
    tests requires 2.3 as it uses the ``DETACH DELETE`` feature to drop the
    database.
``py2neo``
    Currently supports 1.6 and 2.0.
``pyyaml``
    Tested with PyYAML v3.13.

Testing
-------

Running the tests requires an installed, running Neo4j instance. Pass the URL
through the environment variable ``NEO4J_URI``.

Future
------

* Make nodes just dicts with 'labels' and 'properties' keys? Maybe make rels
  dicts with 'head', 'tail', 'type' and 'properties' keys too?
* Add a context manager to register with PyYAML, create graph database
  connection and then cleanup.
* Support locating nodes with a Cypher query as part of creating a
  relationship.
* Add ``gryaml-dump`` CLI tool to render database (or query result) as YAML.
* Test/support ``ruamel.yaml``.
* Add ability to update & display schema.
* Later ``py2neo``.   Dependent mainly on supporting later versions in
  py2neo_compat_.
* Documentation more complete & published to ReadTheDocs.

.. _py2neo_compat: https://pypi.org/project/py2neo-compat/
