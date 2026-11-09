"""Shared fixtures for :mod:`pytest`."""
import os
from collections.abc import Callable
from pathlib import Path

import py2neo
import pytest
import yaml
from py2neo_compat import py2neo_ver

import gryaml

pytest.mark.todo = pytest.mark.xfail(reason='TODO', run=True, strict=True)


def pytest_report_header(config, start_path: Path):
    """Add versions & config info to test output on terminal."""
    lines = []

    if 'NEO4J_URI' in os.environ:
        lines.append(f'Neo4J URI: {os.environ["NEO4J_URI"]}')

    lines.append(f'py2neo: {py2neo.__version__}'
                 f' pyyaml: {yaml.__version__}'
                 f' libyaml: {yaml.__with_libyaml__}')

    return lines


@pytest.fixture
def graphdb() -> py2neo.Graph:
    """Fixture connecting to graphdb."""
    if 'NEO4J_URI' not in os.environ:
        os.environ['NEO4J_URI'] = 'http://localhost:7474/db/data'
    graphdb = gryaml.connect(uri=os.environ['NEO4J_URI'])
    graphdb.delete_all()
    return graphdb


@pytest.fixture
def graphdb_offline() -> None:
    """Ensure the database is not connected."""
    if py2neo_ver < 2:
        pytest.skip('Offline not supported in py2neo < 2')
    neo4j_uri_env = os.environ.get('NEO4J_URI', None)
    if neo4j_uri_env:
        del os.environ['NEO4J_URI']
    old_graphdb = gryaml._py2neo.graphdb
    gryaml._py2neo.graphdb = None
    yield
    gryaml._py2neo.graphdb = old_graphdb
    if neo4j_uri_env:
        os.environ['NEO4J_URI'] = neo4j_uri_env


@pytest.fixture(scope='session')
def samples_path() -> Path:
    return Path(__file__).parent / 'samples'

@pytest.fixture(scope='session')
def sample_file(samples_path: Path) -> Callable[[str], str]:
    def sample_file(fname: str) -> str:
        fname = samples_path / fname
        with fname.open() as f:
            return f.read()
    return sample_file

@pytest.fixture(scope='session')
def sample_yaml(sample_file: Callable[[str], str]) -> Callable[[str], str]:
    def sample_yaml(fname: str) -> str:
        if not fname.endswith(('.yaml', '.yml')):
            fname += '.yaml'
        return sample_file(fname)
    return sample_yaml

