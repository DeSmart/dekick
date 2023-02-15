from os import path

import pytest

from lib.tests.boilerplates import (
    create_flavour,
    delete_boilerplates,
    delete_flavour,
    download_boilerplates_base,
)
from lib.tests.dind import start_dind_container, stop_dind_container
from lib.tests.misc import parse_flavour_version
from lib.tests.registry import start_docker_registry, stop_docker_registry


@pytest.fixture(scope="session", autouse=True)
def start_session(request):
    """Setup boilerplates before running tests"""
    download_boilerplates_base()
    start_docker_registry()
    request.addfinalizer(teardown_session)


def teardown_session():
    """Teardown boilerplates after running tests"""
    stop_docker_registry()
    delete_boilerplates()


@pytest.fixture(scope="function", autouse=True)
def start_function(request):
    """Cleans up boilerplates and stops containers before running test"""
    create_flavour(*parse_flavour_version(path.basename(request.node.fspath)))
    start_dind_container()
    request.addfinalizer(teardown_function)


def teardown_function():
    """Cleans up boilerplates and stops containers after running test"""
    stop_dind_container()
    delete_flavour()
