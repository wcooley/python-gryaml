=============================
gryaml
=============================

..
    .. image:: https://badge.fury.io/py/gryaml.png
        :target: http://badge.fury.io/py/gryaml

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
  rather than just generating abstract/unbound :class:`py2neo.Node` and
  :class:`py2neo.Relationship` objects. This is due to :mod:`py2neo` version
  1.6 not supporting node labels with abstract nodes. This might be changed if
  we are able to migrate off of 1.6 in the near future.

Versions
--------

Python
    Tested with both Python 2.7 and 3.5.
Neo4j
    Should work with anything >= 2.0 but < 3. Tested with 2.3.2. Running the
    tests requires 2.3 as it uses the ``DETACH DELETE`` feature to drop the
    database.
:mod:`py2neo`
    Currently only supports 2.0. Expecting to do 3; dreading 1.6.
:mod:`pyyaml`
    Only tested with PyYAML v3.11, the last release since 2014.

Testing
-------

Running the tests requires an installed, running Neo4j instance. Pass the URL
through the environment variable ``NEO4J_URI``.

Future
------

* Make nodes just dicts with 'labels' and 'properties' keys. Maybe make rels
  dicts with 'head', 'tail', 'type' and 'properties' keys too?
* Make it easier to load without creating in the database?
* Custom YAML representer & constructor. Currently it is not possible to
  automatically dump Node and Relationship objects in a reasonable fashion.
* `py2neo` & Neo4j v3 support.
* Documentation, etc.
