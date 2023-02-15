from os import getcwd, path

import pytest
from filelock import FileLock

from lib.tests.boilerplates import (
    create_flavour,
    delete_flavour,
    download_boilerplates_base,
)
from lib.tests.dind import start_dind_container, stop_dind_container
from lib.tests.misc import parse_flavour_version
from lib.tests.registry import start_docker_registry


def init_session(worker_id):
    """Do some things before workers start"""
    lock = FileLock(getcwd() + "/tmp/pytest.lock", timeout=240)

    if worker_id in ("gw0", "main"):
        start_docker_registry()
        download_boilerplates_base()
        lock.release()
        return

    lock.acquire(timeout=240)


@pytest.fixture(scope="session", autouse=True)
def start_session(worker_id, request):
    """Setup boilerplates before running tests"""
    init_session(worker_id)
    request.addfinalizer(teardown_session)


def teardown_session():
    """Teardown boilerplates after running tests"""
    pass


@pytest.fixture(scope="function", autouse=True)
def start_function(request):
    """Cleans up boilerplates and stops containers before running test"""
    create_flavour(*parse_flavour_version(path.basename(request.node.fspath)))
    start_dind_container()
    request.addfinalizer(teardown_function)


def teardown_function():
    """Cleans up boilerplates and stops containers after running test"""
    delete_flavour()
    stop_dind_container()
