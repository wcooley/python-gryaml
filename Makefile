.PHONY: help clean clean-pyc clean-build lint test test-all docs release sdist

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on multiple Python versions with tox"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package a release"
	@echo "sdist - package"

clean: clean-build clean-pyc

clean-build:
	- rm -fr build/ 
	- rm -fr dist/
	- rm -fr {*/,}*.egg-info
	- rm junit-*.xml
	- rm -r coverage/

clean-pyc:
	# Use '*' to not match .tox
	find */ -name '*.pyc' -o -name '*.pyo' -o -name '*~' -delete
	find */ -name __pycache__ -type d -empty -print0 | xargs -0 rmdir

lint:
	tox -e lint

test:
	py.test

test-all:
	tox

docs:
	rm -f docs/gryaml.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ gryaml
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	python setup.py sdist
	python setup.py bdist_wheel

sdist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
