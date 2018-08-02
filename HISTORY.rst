.. :changelog:

History
-------

0.4.0 (2017-08-30)
++++++++++++++++++

* Enable using application-specific tags ``gryaml.node`` and ``gryaml.rel`` to
  construct instead of PyYAML's general-purpose ``!python/object/apply:``.

0.3.1 (2016-10-28)
++++++++++++++++++

* Fix assumption that a non-*None* instance of
  *GraphDatabaseService* in py2neo 1.6 would not be *False*.

0.3.0 (2016-10-28)
++++++++++++++++++

* Fix so that it should mostly work with py2neo 1.6 in addition to py2neo 2.0.
  py2neo 1.6 does not support abstract nodes without labels, so it must be used
  against a live database, whereas py2neo 2.0 does not. (py2neo v3 support is
  in progress.)

0.2.0 (2016-07-05)
++++++++++++++++++

* Initial implementation of working constructors with some basic testing.

0.1.0 (2015-11-11)
++++++++++++++++++

* First tagged release. No working code, just ideas of what the YAML might look
  like. Not released on PyPI.
